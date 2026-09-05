import asyncio
import logging
import time
from datetime import UTC, datetime

from .automation.manager import AutomationManager
from .clients.base import TorrentClient
from .config import Settings
from .store import Store
from .validator import validate_payload

log = logging.getLogger("rmv")


def torrent_in_scope(
    torrent: dict,
    settings: Settings,
    managed_scopes: frozenset[str] | None = None,
) -> bool:
    scopes = torrent.get("_scopes")
    if not isinstance(scopes, list):
        scopes = []

    normalized = {str(scope).strip().lower() for scope in scopes if str(scope).strip()}
    configured = settings.scopes if managed_scopes is None else managed_scopes

    if not configured:
        return False
    if "*" in configured:
        return bool(normalized)
    return bool(normalized & configured)


def torrent_actionable(torrent: dict, settings: Settings) -> bool:
    state = str(torrent.get("state", "")).lower()
    return bool(settings.action_states) and state in settings.action_states


def torrent_should_inspect(
    torrent: dict,
    settings: Settings,
    managed_scopes: frozenset[str] | None = None,
) -> bool:
    if not torrent_in_scope(torrent, settings, managed_scopes):
        return False
    if settings.torrent_inspect_all_states:
        return True
    return torrent_actionable(torrent, settings)


class ValidationService:
    def __init__(
        self,
        settings: Settings,
        store: Store,
        client: TorrentClient | None,
        client_name: str = "",
        automation: AutomationManager | None = None,
    ):
        self.settings = settings
        self.store = store
        self.client = client
        self.client_name = client_name.strip().lower()
        self.automation = automation
        self.running = False
        self.last_error: str | None = None
        self.last_cycle_at: str | None = None
        self.last_success_at: str | None = None
        self.last_client_version: str | None = None
        self.discovered_scopes: list[str] = []
        self.managed_scopes: frozenset[str] = frozenset()
        self.scope_source = "none"
        self._scope_refresh_monotonic = 0.0
        self._client_lock = asyncio.Lock()
        self.last_seen = 0
        self.last_in_scope = 0
        self.last_actionable = 0
        self.last_validated = 0
        self._load_scope()

    @property
    def configured(self) -> bool:
        return self.client is not None and bool(self.client_name)

    @property
    def display_name(self) -> str:
        if self.client is not None:
            return self.client.display_name
        return "Not configured"

    @property
    def scope_name(self) -> str:
        if self.client is not None:
            return self.client.scope_name
        return "scopes"

    @property
    def supports_delete_data(self) -> bool:
        return bool(self.client is not None and self.client.supports_delete_data)

    def _load_scope(self):
        if self.settings.scopes:
            self.managed_scopes = self.settings.scopes
            self.scope_source = "environment"
            return

        if self.client_name:
            manual = self.store.manual_scopes(self.client_name)
            if manual is not None:
                self.managed_scopes = manual
                self.scope_source = "ui"
                return

            persisted = self.store.bootstrap_scopes(self.client_name)
            if persisted:
                self.managed_scopes = persisted
                self.scope_source = "auto_bootstrap"
                return

        self.managed_scopes = frozenset()
        self.scope_source = "none"

    def set_managed_scopes(self, scopes: list[str]):
        if not self.client_name:
            raise ValueError("Torrent client is not configured.")
        if self.settings.scopes:
            raise ValueError(
                "Managed scopes are controlled by RMV_TORRENT_SCOPES in the environment."
            )

        normalized = frozenset(x.strip().lower() for x in scopes if x.strip())
        self.store.set_manual_scopes(sorted(normalized), self.client_name)
        self.managed_scopes = normalized
        self.scope_source = "ui"

    async def reconfigure(self, client: TorrentClient, client_name: str):
        async with self._client_lock:
            old = self.client
            self.client = client
            self.client_name = client_name.strip().lower()
            self.last_client_version = None
            self.last_error = None
            self.last_success_at = None
            self.discovered_scopes = []
            self._scope_refresh_monotonic = 0.0
            self._load_scope()
            if old is not None:
                await old.close()

    async def refresh_scopes(self, *, force: bool = False):
        if self.client is None:
            return
        refresh_after = max(15, self.settings.torrent_scope_refresh_seconds)
        now = time.monotonic()
        if force or now - self._scope_refresh_monotonic >= refresh_after:
            self.discovered_scopes = await self.client.scopes()
            self._scope_refresh_monotonic = now
            self._maybe_bootstrap_scopes()

    def _maybe_bootstrap_scopes(self):
        if not self.client_name:
            return
        if self.settings.scopes:
            return
        if not self.settings.torrent_auto_bootstrap_scopes:
            return
        if self.store.manual_scopes(self.client_name) is not None:
            return
        if self.store.scope_bootstrap_complete(self.client_name):
            return

        discovered = sorted(
            {x.strip().lower() for x in self.discovered_scopes if x.strip()}
        )
        if not discovered:
            return

        self.store.set_bootstrap_scopes(discovered, self.client_name)
        self.managed_scopes = frozenset(discovered)
        self.scope_source = "auto_bootstrap"
        log.warning(
            "First-run %s bootstrap enabled. RMV added discovered %s to managed scope: %s",
            self.display_name,
            self.scope_name,
            ", ".join(discovered),
        )

    async def run_once(self):
        async with self._client_lock:
            client = self.client
            if client is None:
                self.last_error = None
                self.last_seen = 0
                self.last_in_scope = 0
                self.last_actionable = 0
                self.last_validated = 0
                return

            if self.last_client_version is None:
                self.last_client_version = await client.version()

            await self.refresh_scopes()
            torrents = await client.torrents()
            self.last_seen = len(torrents)
            self.last_in_scope = 0
            self.last_actionable = 0
            self.last_validated = 0

            if not self.managed_scopes:
                log.warning(
                    "No %s are managed for %s. Discovered: %s",
                    self.scope_name,
                    self.display_name,
                    ", ".join(self.discovered_scopes) or "(none)",
                )

            fingerprint = self.settings.policy_fingerprint

            for torrent in torrents:
                torrent_hash = str(torrent.get("hash", ""))
                if not torrent_hash or not torrent_should_inspect(
                    torrent,
                    self.settings,
                    self.managed_scopes,
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

                files = await client.files(torrent_hash)
                if not files:
                    continue

                scope_text = ", ".join(
                    str(x) for x in torrent.get("_scopes", []) if str(x).strip()
                )
                result = validate_payload(
                    torrent_hash=torrent_hash,
                    torrent_name=str(torrent.get("name", "Unknown")),
                    category=scope_text,
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
                    "%s %s [%s/%s]: %s",
                    result.status.upper(),
                    result.torrent_name,
                    self.client_name,
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
                            await client.resume(torrent_hash)
                            action_status = "success"
                    elif (
                        result.status == "blocked"
                        and actionable
                        and self.settings.quarantine_rejected
                    ):
                        action = "quarantine"
                        await client.pause(torrent_hash)
                        action_status = "held"
                        self.store.quarantine_hold(
                            torrent_hash=torrent_hash,
                            torrent_name=result.torrent_name,
                            provider=self.client_name,
                            scopes=result.category,
                            reason=result.reason,
                            at=datetime.now(UTC).isoformat(),
                        )
                        log.warning(
                            "QUARANTINED %s [%s]: %s",
                            result.torrent_name,
                            self.client_name,
                            result.reason,
                        )
                    elif (
                        result.status == "blocked"
                        and actionable
                        and self.settings.remove_rejected
                    ):
                        action = "delete"
                        delete_data = (
                            self.settings.delete_rejected_data
                            and client.supports_delete_data
                        )
                        await client.delete(torrent_hash, delete_data)
                        if (
                            self.settings.delete_rejected_data
                            and not client.supports_delete_data
                        ):
                            action_status = "limited"
                            action_error = (
                                f"{client.display_name} cannot delete local payload data "
                                "through its supported API; the torrent entry was removed only"
                            )
                            log.warning("%s", action_error)
                        else:
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

                if (
                    result.status == "blocked"
                    and actionable
                    and self.automation is not None
                    and self.automation.configured
                    and action_status in {"success", "limited", "held"}
                ):
                    await self.automation.report_rejection(
                        {
                            "torrent_hash": torrent_hash,
                            "torrent_name": result.torrent_name,
                            "provider": self.client_name,
                            "scopes": result.category,
                            "reason": result.reason,
                            "action": action,
                            "action_status": action_status,
                        }
                    )

    async def loop(self):
        self.running = True
        while self.running:
            self.last_cycle_at = datetime.now(UTC).isoformat()
            try:
                await self.run_once()
                if self.configured:
                    self.last_error = None
                    self.last_success_at = datetime.now(UTC).isoformat()
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                self.last_error = str(exc)
                log.exception("Validation cycle failed")
            await asyncio.sleep(max(1, self.settings.poll_seconds))

    def snapshot(self) -> dict:
        bootstrap_complete = (
            self.store.scope_bootstrap_complete(self.client_name)
            if self.client_name
            else False
        )
        return {
            "running": self.running,
            "configured": self.configured,
            "client": self.client_name or None,
            "client_display_name": self.display_name,
            "client_version": self.last_client_version,
            "supports_delete_data": self.supports_delete_data,
            "last_error": self.last_error,
            "last_cycle_at": self.last_cycle_at,
            "last_success_at": self.last_success_at,
            "scope_name": self.scope_name,
            "environment_scopes": sorted(self.settings.scopes),
            "managed_scopes": sorted(self.managed_scopes),
            "discovered_scopes": self.discovered_scopes,
            "scope_source": self.scope_source,
            "scope_bootstrap_complete": bootstrap_complete,
            "scope_auto_bootstrap": self.settings.torrent_auto_bootstrap_scopes,
            "torrents_seen": self.last_seen,
            "in_scope_torrents": self.last_in_scope,
            "actionable_torrents": self.last_actionable,
            "validated_this_cycle": self.last_validated,
            "policy_fingerprint": self.settings.policy_fingerprint,
            "quarantine_rejected": self.settings.quarantine_rejected,
            "quarantined": self.store.quarantine_count(),
            "automation_configured": bool(self.automation and self.automation.configured),
            "automation_instances": (
                len(self.automation.providers) if self.automation is not None else 0
            ),
            "automation_last_results": (
                self.automation.last_results if self.automation is not None else []
            ),
        }

    async def close(self):
        if self.automation is not None:
            await self.automation.close()
        async with self._client_lock:
            if self.client is not None:
                await self.client.close()
                self.client = None

    def stop(self):
        self.running = False
