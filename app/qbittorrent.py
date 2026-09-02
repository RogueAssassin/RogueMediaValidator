import httpx


class QBittorrentClient:
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.client = httpx.AsyncClient(timeout=15)
        self._logged_in = False

    async def close(self):
        await self.client.aclose()

    async def login(self, *, force: bool = False):
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

    async def app_version(self) -> str:
        r = await self._request("GET", "/api/v2/app/version")
        return r.text.strip() or "unknown"

    async def torrents(self) -> list[dict]:
        r = await self._request("GET", "/api/v2/torrents/info")
        return r.json()

    async def files(self, torrent_hash: str) -> list[dict]:
        r = await self._request(
            "GET", "/api/v2/torrents/files", params={"hash": torrent_hash}
        )
        return r.json()

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
