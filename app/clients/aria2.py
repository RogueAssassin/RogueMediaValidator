import httpx


class Aria2Client:
    provider_id = "aria2"
    display_name = "aria2"
    scope_name = "download paths"
    supports_delete_data = False

    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip("/")
        self.secret = password
        timeout = httpx.Timeout(15.0, connect=5.0)
        transport = httpx.AsyncHTTPTransport(retries=2)
        self.client = httpx.AsyncClient(
            timeout=timeout,
            transport=transport,
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
        )
        self._request_id = 0

    async def close(self):
        await self.client.aclose()

    async def _rpc(self, method: str, params: list | None = None):
        self._request_id += 1
        call_params = list(params or [])
        if self.secret:
            call_params.insert(0, f"token:{self.secret}")
        response = await self.client.post(
            self.base_url,
            json={
                "jsonrpc": "2.0",
                "id": str(self._request_id),
                "method": method,
                "params": call_params,
            },
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise TypeError("aria2 returned an invalid JSON-RPC response")
        if payload.get("error"):
            error = payload["error"]
            message = error.get("message", str(error)) if isinstance(error, dict) else str(error)
            raise RuntimeError(f"aria2 RPC error: {message}")
        return payload.get("result")

    async def version(self) -> str:
        result = await self._rpc("aria2.getVersion")
        if not isinstance(result, dict):
            raise TypeError("aria2 returned an invalid version response")
        return str(result.get("version") or "unknown")

    @staticmethod
    def _keys() -> list[str]:
        return ["gid", "status", "totalLength", "completedLength", "dir", "bittorrent"]

    async def _downloads(self) -> list[dict]:
        keys = self._keys()
        groups = [
            await self._rpc("aria2.tellActive", [keys]),
            await self._rpc("aria2.tellWaiting", [0, 1000, keys]),
            await self._rpc("aria2.tellStopped", [0, 1000, keys]),
        ]
        merged = {}
        for group in groups:
            if not isinstance(group, list):
                continue
            for item in group:
                if not isinstance(item, dict) or "bittorrent" not in item:
                    continue
                gid = str(item.get("gid", ""))
                if gid:
                    merged[gid] = item
        return list(merged.values())

    @staticmethod
    def _scope_values(item: dict) -> list[str]:
        path = str(item.get("dir", "")).strip()
        return [path] if path else []

    @staticmethod
    def _normalize_state(item: dict) -> str:
        status = str(item.get("status", "")).lower()
        total = int(item.get("totalLength", 0) or 0)
        completed = int(item.get("completedLength", 0) or 0)
        done = total > 0 and completed >= total
        if status == "active":
            return "uploading" if done else "downloading"
        if status == "waiting":
            return "queuedup" if done else "queueddl"
        if status == "paused":
            return "stoppedup" if done else "stoppeddl"
        if status == "complete":
            return "stoppedup"
        if status in {"error", "removed"}:
            return "stoppedup" if done else "stoppeddl"
        return status or "unknown"

    async def scopes(self) -> list[str]:
        downloads = await self._downloads()
        return sorted(
            {
                scope
                for item in downloads
                for scope in self._scope_values(item)
            }
        )

    async def torrents(self) -> list[dict]:
        downloads = await self._downloads()
        normalized = []
        for item in downloads:
            bittorrent = item.get("bittorrent") or {}
            info = bittorrent.get("info") if isinstance(bittorrent, dict) else {}
            name = info.get("name") if isinstance(info, dict) else None
            scopes = self._scope_values(item)
            normalized.append(
                {
                    "hash": str(item.get("gid", "")),
                    "name": str(name or item.get("gid", "Unknown")),
                    "category": scopes[0] if scopes else "",
                    "_scopes": scopes,
                    "state": self._normalize_state(item),
                }
            )
        return normalized

    async def files(self, torrent_hash: str) -> list[dict]:
        result = await self._rpc("aria2.tellStatus", [torrent_hash, ["files"]])
        if not isinstance(result, dict):
            return []
        files = result.get("files", [])
        return [
            {
                "name": str(item.get("path", "")),
                "size": int(item.get("length", 0) or 0),
            }
            for item in files
            if isinstance(item, dict)
        ]

    async def resume(self, torrent_hash: str):
        await self._rpc("aria2.unpause", [torrent_hash])

    async def delete(self, torrent_hash: str, delete_files: bool):
        await self._rpc("aria2.remove", [torrent_hash])
