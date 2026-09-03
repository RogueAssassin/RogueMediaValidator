import httpx


class TransmissionClient:
    provider_id = "transmission"
    display_name = "Transmission"
    scope_name = "labels"
    supports_delete_data = True

    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        auth = httpx.BasicAuth(username, password) if username or password else None
        timeout = httpx.Timeout(15.0, connect=5.0)
        transport = httpx.AsyncHTTPTransport(retries=2)
        self.client = httpx.AsyncClient(
            auth=auth,
            timeout=timeout,
            transport=transport,
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
        )
        self._session_id: str | None = None
        self._protocol: str | None = None
        self._request_id = 0

    async def close(self):
        await self.client.aclose()

    async def _post(self, payload: dict) -> dict:
        headers = {}
        if self._session_id:
            headers["X-Transmission-Session-Id"] = self._session_id

        response = await self.client.post(self.base_url, json=payload, headers=headers)
        if response.status_code == 409:
            session_id = response.headers.get("X-Transmission-Session-Id")
            if not session_id:
                raise RuntimeError("Transmission did not return a CSRF session id")
            self._session_id = session_id
            headers["X-Transmission-Session-Id"] = session_id
            response = await self.client.post(self.base_url, json=payload, headers=headers)

        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):
            raise TypeError("Transmission returned an invalid RPC response")
        return data

    async def _modern_call(self, method: str, params: dict | None = None) -> dict:
        self._request_id += 1
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": self._request_id,
        }
        data = await self._post(payload)
        if "error" in data:
            error = data.get("error") or {}
            raise RuntimeError(
                f"Transmission RPC error: {error.get('message', 'unknown error')}"
            )
        result = data.get("result", {})
        if not isinstance(result, dict):
            raise TypeError("Transmission returned an invalid result object")
        return result

    async def _legacy_call(self, method: str, arguments: dict | None = None) -> dict:
        data = await self._post({"method": method, "arguments": arguments or {}})
        if data.get("result") != "success":
            raise RuntimeError(
                f"Transmission RPC error: {data.get('result', 'unknown error')}"
            )
        arguments_out = data.get("arguments", {})
        if not isinstance(arguments_out, dict):
            raise TypeError("Transmission returned invalid legacy arguments")
        return arguments_out

    async def _detect_protocol(self):
        if self._protocol:
            return

        try:
            result = await self._modern_call("session_get", {"fields": ["version"]})
            if result.get("version"):
                self._protocol = "modern"
                return
        except (httpx.HTTPError, RuntimeError, TypeError, ValueError):
            pass

        result = await self._legacy_call("session-get")
        if not result.get("version"):
            raise RuntimeError("Unable to determine Transmission RPC version")
        self._protocol = "legacy"

    async def _call(
        self,
        modern_method: str,
        modern_params: dict | None = None,
        *,
        legacy_method: str | None = None,
        legacy_arguments: dict | None = None,
    ) -> dict:
        await self._detect_protocol()
        if self._protocol == "modern":
            return await self._modern_call(modern_method, modern_params)
        return await self._legacy_call(
            legacy_method or modern_method.replace("_", "-"),
            legacy_arguments if legacy_arguments is not None else modern_params,
        )

    async def version(self) -> str:
        await self._detect_protocol()
        if self._protocol == "modern":
            result = await self._modern_call(
                "session_get", {"fields": ["version", "rpc_version_semver"]}
            )
        else:
            result = await self._legacy_call("session-get")
        return str(result.get("version") or "unknown")

    async def scopes(self) -> list[str]:
        torrents = await self.torrents()
        labels = {
            str(label).strip()
            for torrent in torrents
            for label in torrent.get("_scopes", [])
            if str(label).strip()
        }
        return sorted(labels)

    async def torrents(self) -> list[dict]:
        await self._detect_protocol()
        if self._protocol == "modern":
            result = await self._modern_call(
                "torrent_get",
                {
                    "fields": [
                        "hash_string",
                        "name",
                        "labels",
                        "status",
                        "percent_complete",
                    ]
                },
            )
            raw = result.get("torrents", [])
            hash_key = "hash_string"
            percent_key = "percent_complete"
        else:
            result = await self._legacy_call(
                "torrent-get",
                {
                    "fields": [
                        "hashString",
                        "name",
                        "labels",
                        "status",
                        "percentDone",
                    ]
                },
            )
            raw = result.get("torrents", [])
            hash_key = "hashString"
            percent_key = "percentDone"

        normalized = []
        for torrent in raw:
            labels = [
                str(x).strip()
                for x in torrent.get("labels", [])
                if str(x).strip()
            ]
            percent = float(torrent.get(percent_key, 0) or 0)
            state = self._normalize_state(int(torrent.get("status", 0) or 0), percent)
            normalized.append(
                {
                    "hash": str(torrent.get(hash_key, "")),
                    "name": str(torrent.get("name", "Unknown")),
                    "category": labels[0] if labels else "",
                    "_scopes": labels,
                    "state": state,
                }
            )
        return normalized

    @staticmethod
    def _normalize_state(status: int, percent_complete: float) -> str:
        if status == 0:
            return "stoppedup" if percent_complete >= 1 else "stoppeddl"
        if status in {1, 2}:
            return "checkingdl"
        if status == 3:
            return "queueddl"
        if status == 4:
            return "downloading"
        if status == 5:
            return "queuedup"
        if status == 6:
            return "uploading"
        return "unknown"

    async def files(self, torrent_hash: str) -> list[dict]:
        await self._detect_protocol()
        if self._protocol == "modern":
            result = await self._modern_call(
                "torrent_get",
                {"ids": [torrent_hash], "fields": ["files"]},
            )
        else:
            result = await self._legacy_call(
                "torrent-get",
                {"ids": [torrent_hash], "fields": ["files"]},
            )
        torrents = result.get("torrents", [])
        if not torrents:
            return []
        return [
            {"name": str(item.get("name", "")), "size": int(item.get("length", 0) or 0)}
            for item in torrents[0].get("files", [])
        ]

    async def resume(self, torrent_hash: str):
        await self._call(
            "torrent_start",
            {"ids": [torrent_hash]},
            legacy_method="torrent-start",
            legacy_arguments={"ids": [torrent_hash]},
        )

    async def delete(self, torrent_hash: str, delete_files: bool):
        await self._call(
            "torrent_remove",
            {"ids": [torrent_hash], "delete_local_data": delete_files},
            legacy_method="torrent-remove",
            legacy_arguments={"ids": [torrent_hash], "delete-local-data": delete_files},
        )
