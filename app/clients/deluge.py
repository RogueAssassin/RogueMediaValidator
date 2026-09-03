import httpx


class DelugeClient:
    provider_id = "deluge"
    display_name = "Deluge"
    scope_name = "labels / download paths"
    supports_delete_data = True

    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip("/")
        if not self.base_url.endswith("/json"):
            self.base_url += "/json"
        self.username = username
        self.password = password
        timeout = httpx.Timeout(15.0, connect=5.0)
        transport = httpx.AsyncHTTPTransport(retries=2)
        self.client = httpx.AsyncClient(
            timeout=timeout,
            transport=transport,
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
        )
        self._request_id = 0
        self._authenticated = False
        self._daemon_ready = False

    async def close(self):
        await self.client.aclose()

    async def _rpc(self, method: str, params: list | None = None):
        self._request_id += 1
        response = await self.client.post(
            self.base_url,
            json={"method": method, "params": params or [], "id": self._request_id},
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise TypeError("Deluge returned an invalid JSON-RPC response")
        if payload.get("error"):
            error = payload["error"]
            message = error.get("message", str(error)) if isinstance(error, dict) else str(error)
            raise RuntimeError(f"Deluge RPC error: {message}")
        return payload.get("result")

    async def _ensure_authenticated(self):
        if self._authenticated:
            return
        if not self.password:
            raise RuntimeError("Deluge Web UI password is required")
        result = await self._rpc("auth.login", [self.password])
        if result is not True:
            raise RuntimeError("Deluge authentication failed")
        self._authenticated = True

    async def _ensure_daemon(self):
        await self._ensure_authenticated()
        if self._daemon_ready:
            return
        if await self._rpc("web.connected"):
            self._daemon_ready = True
            return

        hosts = await self._rpc("web.get_hosts")
        if not isinstance(hosts, list) or not hosts:
            raise RuntimeError("Deluge Web has no configured daemon hosts")

        for host in hosts:
            if not isinstance(host, (list, tuple)) or not host:
                continue
            host_id = str(host[0])
            try:
                await self._rpc("web.connect", [host_id])
                if await self._rpc("web.connected"):
                    self._daemon_ready = True
                    return
            except (RuntimeError, httpx.HTTPError):
                continue
        raise RuntimeError("Deluge Web could not connect to a deluged host")

    async def version(self) -> str:
        await self._ensure_daemon()
        result = await self._rpc("core.get_version")
        return str(result or "unknown")

    async def _torrent_map(self) -> dict:
        await self._ensure_daemon()
        keys = ["name", "state", "progress", "label", "download_location"]
        try:
            result = await self._rpc("core.get_torrents_status", [{}, keys])
        except RuntimeError:
            keys = ["name", "state", "progress", "download_location"]
            result = await self._rpc("core.get_torrents_status", [{}, keys])
        if not isinstance(result, dict):
            raise TypeError("Deluge returned an invalid torrent list")
        return result

    async def scopes(self) -> list[str]:
        torrents = await self._torrent_map()
        scopes = {
            scope
            for status in torrents.values()
            if isinstance(status, dict)
            for scope in self._scope_values(status)
        }
        return sorted(scopes)

    @staticmethod
    def _scope_values(status: dict) -> list[str]:
        label = str(status.get("label", "")).strip()
        if label:
            return [label]
        path = str(status.get("download_location", "")).strip()
        return [path] if path else []

    @staticmethod
    def _normalize_state(state: str, progress: float) -> str:
        lowered = state.strip().lower()
        if lowered in {"downloading", "allocating"}:
            return "downloading"
        if lowered in {"checking", "checking resume data"}:
            return "checkingdl"
        if lowered in {"queued", "queued downloading"}:
            return "queueddl" if progress < 100 else "queuedup"
        if lowered in {"seeding", "active"} and progress >= 100:
            return "uploading"
        if lowered in {"paused", "stopped"}:
            return "stoppedup" if progress >= 100 else "stoppeddl"
        if lowered == "error":
            return "stoppeddl"
        return lowered.replace(" ", "") or "unknown"

    async def torrents(self) -> list[dict]:
        raw = await self._torrent_map()
        normalized = []
        for torrent_hash, status in raw.items():
            if not isinstance(status, dict):
                continue
            progress = float(status.get("progress", 0) or 0)
            scopes = self._scope_values(status)
            normalized.append(
                {
                    "hash": str(torrent_hash),
                    "name": str(status.get("name", "Unknown")),
                    "category": scopes[0] if scopes else "",
                    "_scopes": scopes,
                    "state": self._normalize_state(str(status.get("state", "")), progress),
                }
            )
        return normalized

    async def files(self, torrent_hash: str) -> list[dict]:
        await self._ensure_daemon()
        result = await self._rpc("core.get_torrent_status", [torrent_hash, ["files"]])
        if not isinstance(result, dict):
            return []
        files = result.get("files", [])
        return [
            {
                "name": str(item.get("path", item.get("name", ""))),
                "size": int(item.get("size", 0) or 0),
            }
            for item in files
            if isinstance(item, dict)
        ]

    async def resume(self, torrent_hash: str):
        await self._ensure_daemon()
        await self._rpc("core.resume_torrent", [torrent_hash])

    async def delete(self, torrent_hash: str, delete_files: bool):
        await self._ensure_daemon()
        result = await self._rpc("core.remove_torrent", [torrent_hash, delete_files])
        if result is not True:
            raise RuntimeError("Deluge did not confirm torrent removal")
