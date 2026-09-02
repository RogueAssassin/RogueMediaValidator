import asyncio
import logging

from .config import Settings
from .qbittorrent import QBittorrentClient
from .store import Store
from .validator import validate_payload

log = logging.getLogger("rmv")


class ValidationService:
    def __init__(self, settings: Settings, store: Store, qb: QBittorrentClient):
        self.settings = settings
        self.store = store
        self.qb = qb
        self.running = False
        self.last_error: str | None = None

    async def run_once(self):
        torrents = await self.qb.torrents()
        for torrent in torrents:
            torrent_hash = str(torrent.get("hash", ""))
            category = str(torrent.get("category", ""))
            if not torrent_hash or self.store.has(torrent_hash):
                continue
            if self.settings.categories and category.lower() not in self.settings.categories:
                continue

            files = await self.qb.files(torrent_hash)
            if not files:
                continue

            result = validate_payload(
                torrent_hash=torrent_hash,
                torrent_name=str(torrent.get("name", "Unknown")),
                category=category,
                files=files,
                settings=self.settings,
            )
            self.store.save(result)
            log.info("%s %s: %s", result.status.upper(), result.torrent_name, result.reason)

            if self.settings.dry_run:
                continue
            if result.status == "approved" and self.settings.auto_resume_valid:
                await self.qb.resume(torrent_hash)
            elif result.status == "blocked" and self.settings.remove_rejected:
                await self.qb.delete(torrent_hash, self.settings.delete_rejected_data)

    async def loop(self):
        self.running = True
        while self.running:
            try:
                await self.run_once()
                self.last_error = None
            except Exception as exc:
                self.last_error = str(exc)
                log.exception("Validation cycle failed")
            await asyncio.sleep(max(1, self.settings.poll_seconds))

    def stop(self):
        self.running = False
