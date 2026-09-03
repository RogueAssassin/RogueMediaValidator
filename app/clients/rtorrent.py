from xmlrpc.client import dumps, loads

import httpx


class RTorrentClient:
    provider_id = "rtorrent"
    display_name = "rTorrent / ruTorrent"
    scope_name = "labels / download paths"
    supports_delete_data = False

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
            headers={"Content-Type": "text/xml"},
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
        )

    async def close(self):
        await self.client.aclose()

    async def _rpc(self, method: str, *params):
        body = dumps(params, methodname=method, allow_none=True)
        response = await self.client.post(self.base_url, content=body.encode())
        response.raise_for_status()
        values, _ = loads(response.content)
        return values[0] if values else None

    async def version(self) -> str:
        result = await self._rpc("system.client_version")
        return str(result or "unknown")

    async def _rows(self) -> list:
        result = await self._rpc(
            "d.multicall2",
            "",
            "main",
            "d.hash=",
            "d.name=",
            "d.custom1=",
            "d.directory=",
            "d.is_active=",
            "d.complete=",
            "d.is_hash_checking=",
        )
        if not isinstance(result, (list, tuple)):
            raise TypeError("rTorrent returned an invalid download list")
        return list(result)

    @staticmethod
    def _scope_values(custom1, directory) -> list[str]:
        label = str(custom1 or "").strip()
        if label:
            return [label]
        path = str(directory or "").strip()
        return [path] if path else []

    @staticmethod
    def _normalize_state(active: int, complete: int, hashing: int) -> str:
        if int(hashing or 0):
            return "checkingdl"
        if int(active or 0):
            return "uploading" if int(complete or 0) else "downloading"
        return "stoppedup" if int(complete or 0) else "stoppeddl"

    async def scopes(self) -> list[str]:
        rows = await self._rows()
        scopes = {
            scope
            for row in rows
            if isinstance(row, (list, tuple)) and len(row) >= 7
            for scope in self._scope_values(row[2], row[3])
        }
        return sorted(scopes)

    async def torrents(self) -> list[dict]:
        rows = await self._rows()
        normalized = []
        for row in rows:
            if not isinstance(row, (list, tuple)) or len(row) < 7:
                continue
            scopes = self._scope_values(row[2], row[3])
            normalized.append(
                {
                    "hash": str(row[0]),
                    "name": str(row[1] or "Unknown"),
                    "category": scopes[0] if scopes else "",
                    "_scopes": scopes,
                    "state": self._normalize_state(row[4], row[5], row[6]),
                }
            )
        return normalized

    async def files(self, torrent_hash: str) -> list[dict]:
        result = await self._rpc(
            "f.multicall",
            torrent_hash,
            "",
            "f.path=",
            "f.size_bytes=",
        )
        if not isinstance(result, (list, tuple)):
            return []
        files = []
        for row in result:
            if not isinstance(row, (list, tuple)) or len(row) < 2:
                continue
            files.append({"name": str(row[0]), "size": int(row[1] or 0)})
        return files

    async def resume(self, torrent_hash: str):
        await self._rpc("d.start", torrent_hash)

    async def delete(self, torrent_hash: str, delete_files: bool):
        await self._rpc("d.erase", torrent_hash)
