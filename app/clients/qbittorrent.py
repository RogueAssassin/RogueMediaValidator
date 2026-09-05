import asyncio

import httpx


class QBittorrentClient:
    provider_id = "qbittorrent"
    display_name = "qBittorrent"
    scope_name = "categories"
    supports_delete_data = True

    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        timeout = httpx.Timeout(15.0, connect=5.0)
        transport = httpx.AsyncHTTPTransport(retries=2)
        self.client = httpx.AsyncClient(
            timeout=timeout,
            transport=transport,
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
        )
        self._logged_in = False
        self._login_lock = asyncio.Lock()

    async def close(self):
        await self.client.aclose()

    async def login(self, *, force: bool = False):
        async with self._login_lock:
            if self._logged_in and not force:
                return

            r = await self.client.post(
                f"{self.base_url}/api/v2/auth/login",
                data={"username": self.username, "password": self.password},
            )
            r.raise_for_status()
            body = r.text.strip()
            if body and body != "Ok.":
                self._logged_in = False
                raise RuntimeError("qBittorrent authentication failed")
            self._logged_in = True

    async def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        await self.login()
        r = await self.client.request(method, f"{self.base_url}{path}", **kwargs)
        if r.status_code in {401, 403}:
            self._logged_in = False
            await self.login(force=True)
            r = await self.client.request(method, f"{self.base_url}{path}", **kwargs)
        r.raise_for_status()
        return r

    async def version(self) -> str:
        r = await self._request("GET", "/api/v2/app/version")
        return r.text.strip() or "unknown"

    async def app_version(self) -> str:
        return await self.version()

    async def scopes(self) -> list[str]:
        r = await self._request("GET", "/api/v2/torrents/categories")
        payload = r.json()
        if not isinstance(payload, dict):
            raise TypeError("qBittorrent returned an invalid category response")
        return sorted(str(name) for name in payload if str(name).strip())

    async def categories(self) -> list[str]:
        return await self.scopes()

    async def torrents(self) -> list[dict]:
        r = await self._request("GET", "/api/v2/torrents/info")
        torrents = r.json()
        for torrent in torrents:
            category = str(torrent.get("category", "")).strip()
            torrent["_scopes"] = [category] if category else []
        return torrents

    async def files(self, torrent_hash: str) -> list[dict]:
        r = await self._request(
            "GET", "/api/v2/torrents/files", params={"hash": torrent_hash}
        )
        return r.json()

    async def pause(self, torrent_hash: str):
        await self._request(
            "POST", "/api/v2/torrents/stop", data={"hashes": torrent_hash}
        )

    async def resume(self, torrent_hash: str):
        await self._request(
            "POST", "/api/v2/torrents/start", data={"hashes": torrent_hash}
        )

    async def delete(self, torrent_hash: str, delete_files: bool):
        await self._request(
            "POST",
            "/api/v2/torrents/delete",
            data={"hashes": torrent_hash, "deleteFiles": str(delete_files).lower()},
        )
