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

    async def login(self):
        if self._logged_in:
            return

        r = await self.client.post(
            f"{self.base_url}/api/v2/auth/login",
            data={"username": self.username, "password": self.password},
        )
        r.raise_for_status()

        # qBittorrent commonly returns "Ok." on success. Some deployments or
        # proxies return a successful 204 No Content instead, so treat any 2xx
        # response with an empty body as successful. Explicit non-empty failure
        # responses remain rejected.
        body = r.text.strip()
        if body and body != "Ok.":
            raise RuntimeError("qBittorrent authentication failed")

        self._logged_in = True

    async def torrents(self) -> list[dict]:
        await self.login()
        r = await self.client.get(f"{self.base_url}/api/v2/torrents/info")
        r.raise_for_status()
        return r.json()

    async def files(self, torrent_hash: str) -> list[dict]:
        await self.login()
        r = await self.client.get(
            f"{self.base_url}/api/v2/torrents/files", params={"hash": torrent_hash}
        )
        r.raise_for_status()
        return r.json()

    async def resume(self, torrent_hash: str):
        await self.login()
        r = await self.client.post(
            f"{self.base_url}/api/v2/torrents/start",
            data={"hashes": torrent_hash},
        )
        r.raise_for_status()

    async def delete(self, torrent_hash: str, delete_files: bool):
        await self.login()
        r = await self.client.post(
            f"{self.base_url}/api/v2/torrents/delete",
            data={"hashes": torrent_hash, "deleteFiles": str(delete_files).lower()},
        )
        r.raise_for_status()
