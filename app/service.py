import asyncio
import logging
import time
from datetime import UTC, datetime

from .config import Settings
from .qbittorrent import QBittorrentClient
from .store import Store
from .validator import validate_payload

log = logging.getLogger("rmv")


def torrent_in_scope(
    torrent: dict,
    settings: Settings,
    managed_categories: frozenset[str] | None = None,
) -> bool:
    category = str(torrent.get("category", "")).strip().lower()
    categories = settings.categories if managed_categories is None else managed_categories
    if not categories:
        return False
    if "*" in categories:
        return bool(category)
    return category in categories


def torrent_actionable(torrent: dict, settings: Settings) -> bool:
    state = str(torrent.get("state", "")).lower()
    return bool(settings.action_states) and state in settings.action_states


def torrent_should_inspect(
    torrent: dict,
    settings: Settings,
    managed_categories: frozenset[str] | None = None,
) -> bool:
    if not torrent_in_scope(torrent, settings, managed_categories):
        return False
    if settings.qb_inspect_all_states:
        return True
    return torrent_actionable(torrent, settings)


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
        self.discovered_categories: list[str] = []
        self.managed_categories: frozenset[str] = frozenset()
        self.category_source = "none"
        self._category_refresh_monotonic = 0.0
        self.last_seen = 0
        self.last_in_scope = 0
        self.last_actionable = 0
        self.last_validated = 0
        self._load_category_scope()

    def _load_category_scope(self):
        if self.settings.categories:
            self.managed_categories = self.settings.categories
            self.category_source = "environment"
            return

        persisted = self.store.bootstrap_categories()
        if persisted:
            self.managed_categories = persisted
            self.category_source = "auto_bootstrap"
            return

        self.managed_categories = frozenset()
        self.category_source = "none"

    async def refresh_categories(self, *, force: bool = False):
        refresh_after = max(15, self.settings.qb_category_refresh_seconds)
        now = time.monotonic()
        if force or now - self._category_refresh_monotonic >= refresh_after:
            self.discovered_categories = await self.qb.categories()
            self._category_refresh_monotonic = now
            self._maybe_bootstrap_categories()

    def _maybe_bootstrap_categories(self):
        if self.settings.categories:
            return
        if not self.settings.qb_auto_bootstrap_categories:
            return
        if self.store.category_bootstrap_complete():
            return

        discovered = sorted(
            {x.strip().lower() for x in self.discovered_categories if x.strip()}
        )
        if not discovered:
            return

        self.store.set_bootstrap_categories(discovered)
        self.managed_categories = frozenset(discovered)
        self.category_source = "auto_bootstrap"
        log.warning(
            "First-run category bootstrap enabled. RMV automatically added discovered "
            "qBittorrent categories to managed scope: %s",
            ", ".join(discovered),
        )

    async def run_once(self):
        if self.last_qb_version is None:
            self.last_qb_version = await self.qb.app_version()

        await self.refresh_categories()
        torrents = await self.qb.torrents()
        self.last_seen = len(torrents)
        self.last_in_scope = 0
        self.last_actionable = 0
        self.last_validated = 0

        if not self.managed_categories:
            log.warning(
                "No qBittorrent categories are managed. Discovered categories: %s",
                ", ".join(self.discovered_categories) or "(none)",
            )

        fingerprint = self.settings.policy_fingerprint

        for torrent in torrents:
            torrent_hash = str(torrent.get("hash", ""))
            if not torrent_hash or not torrent_should_inspect(
                torrent,
                self.settings,
                self.managed_categories,
            ):
                continue

            self.last_in_scope += 1
            actionable = torrent_actionable(torrent, self.settings)
            if actionable:
                self.last_actionable += 1

            if self.settings.dry_run:
                if self.store.has_current(torrent_hash, fingerprint):
                    continue
            elif self.store.has_enforced_current(torrent_hash, fingerprint):
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
            self.store.save(
                result,
                policy_fingerprint=fingerprint,
                enforced=False,
                action="none",
                action_status="audit",
            )
            self.last_validated += 1
            state = str(torrent.get("state", "unknown"))
            log.info(
                "%s %s [%s]: %s",
                result.status.upper(),
                result.torrent_name,
                state,
                result.reason,
            )

            if self.settings.dry_run:
                continue

            action = "none"
            action_status = "not_required"
            action_error = None

            try:
                if result.status == "approved":
                    if (
                        actionable
                        and state.lower() in {"pauseddl", "stoppeddl"}
                        and self.settings.auto_resume_valid
                    ):
                        action = "resume"
                        await self.qb.resume(torrent_hash)
                        action_status = "success"
                elif (
                    result.status == "blocked"
                    and actionable
                    and self.settings.remove_rejected
                ):
                    action = "delete"
                    await self.qb.delete(torrent_hash, self.settings.delete_rejected_data)
                    action_status = "success"
                elif result.status == "blocked" and not actionable:
                    action_status = "inspection_only"
                    log.warning(
                        "BLOCKED payload found in non-actionable state %s for %s; "
                        "recorded only, no torrent action taken",
                        state,
                        result.torrent_name,
                    )
            except Exception as exc:
                action_status = "failed"
                action_error = str(exc)
                self.store.save(
                    result,
                    policy_fingerprint=fingerprint,
                    enforced=False,
                    action=action,
                    action_status=action_status,
                    action_error=action_error,
                )
                raise

            self.store.save(
                result,
                policy_fingerprint=fingerprint,
                enforced=True,
                action=action,
                action_status=action_status,
                action_error=action_error,
            )

    async def loop(self):
        self.running = True
        while self.running:
            self.last_cycle_at = datetime.now(UTC).isoformat()
            try:
                await self.run_once()
                self.last_error = None
                self.last_success_at = datetime.now(UTC).isoformat()
            except asyncio.CancelledError:
                raise
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
            "environment_categories": sorted(self.settings.categories),
            "managed_categories": sorted(self.managed_categories),
            "discovered_categories": self.discovered_categories,
            "category_source": self.category_source,
            "category_bootstrap_complete": self.store.category_bootstrap_complete(),
            "category_auto_bootstrap": self.settings.qb_auto_bootstrap_categories,
            "torrents_seen": self.last_seen,
            "in_scope_torrents": self.last_in_scope,
            "actionable_torrents": self.last_actionable,
            "validated_this_cycle": self.last_validated,
            "policy_fingerprint": self.settings.policy_fingerprint,
        }

    def stop(self):
        self.running = False
