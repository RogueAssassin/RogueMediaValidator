import asyncio
import logging
from datetime import UTC, datetime

from .config import Settings
from .qbittorrent import QBittorrentClient
from .store import Store
from .validator import validate_payload

log = logging.getLogger("rmv")


def torrent_is_eligible(torrent: dict, settings: Settings) -> bool:
    category = str(torrent.get("category", "")).lower()
    state = str(torrent.get("state", "")).lower()

    if settings.categories and category not in settings.categories:
        return False
    return not settings.managed_states or state in settings.managed_states


class ValidationService:
    def __init__(self, settings: Settings, store: Store, qb: QBittorrentClient):
        self.settings = settings
        self.store = store
        self.qb = qb
        self.running = False
        self.last_error: str | None = None
        self.last_cycle_at: str | None = None
        self.last_success_at: str | None = None
        self.last_qb_version: str | None = None
        self.last_seen = 0
        self.last_eligible = 0
        self.last_validated = 0

    async def run_once(self):
        if self.last_qb_version is None:
            self.last_qb_version = await self.qb.app_version()

        torrents = await self.qb.torrents()
        self.last_seen = len(torrents)
        self.last_eligible = 0
        self.last_validated = 0

        for torrent in torrents:
            torrent_hash = str(torrent.get("hash", ""))
            if not torrent_hash or not torrent_is_eligible(torrent, self.settings):
                continue

            self.last_eligible += 1
            if self.settings.dry_run:
                if self.store.has(torrent_hash):
                    continue
            elif self.store.has_enforced(torrent_hash):
                continue

            files = await self.qb.files(torrent_hash)
            if not files:
                continue

            result = validate_payload(
                torrent_hash=torrent_hash,
                torrent_name=str(torrent.get("name", "Unknown")),
                category=str(torrent.get("category", "")),
                files=files,
                settings=self.settings,
            )
            self.store.save(result, enforced=False)
            self.last_validated += 1
            log.info("%s %s: %s", result.status.upper(), result.torrent_name, result.reason)

            if self.settings.dry_run:
                continue

            if result.status == "approved" and self.settings.auto_resume_valid:
                await self.qb.resume(torrent_hash)
            elif result.status == "blocked" and self.settings.remove_rejected:
                await self.qb.delete(torrent_hash, self.settings.delete_rejected_data)

            self.store.save(result, enforced=True)

    async def loop(self):
        self.running = True
        while self.running:
            self.last_cycle_at = datetime.now(UTC).isoformat()
            try:
                await self.run_once()
                self.last_error = None
                self.last_success_at = datetime.now(UTC).isoformat()
            except Exception as exc:
                self.last_error = str(exc)
                log.exception("Validation cycle failed")
            await asyncio.sleep(max(1, self.settings.poll_seconds))

    def snapshot(self) -> dict:
        return {
            "running": self.running,
            "last_error": self.last_error,
            "last_cycle_at": self.last_cycle_at,
            "last_success_at": self.last_success_at,
            "qbittorrent_version": self.last_qb_version,
            "torrents_seen": self.last_seen,
            "eligible_torrents": self.last_eligible,
            "validated_this_cycle": self.last_validated,
        }

    def stop(self):
        self.running = False
