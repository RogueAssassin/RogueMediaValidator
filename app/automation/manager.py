import logging

from .base import AutomationProvider

log = logging.getLogger("rmv.automation")


class AutomationManager:
    def __init__(self, providers: list[AutomationProvider], store):
        self.providers = providers
        self.store = store
        self.last_results: list[dict] = []

    @property
    def configured(self) -> bool:
        return bool(self.providers)

    async def close(self):
        for provider in self.providers:
            await provider.close()

    async def test_all(self) -> list[dict]:
        results = []
        for provider in self.providers:
            try:
                data = await provider.test()
                results.append({"ok": True, **data})
            except Exception as exc:
                results.append(
                    {
                        "ok": False,
                        "provider": provider.provider_id,
                        "instance": provider.instance_name,
                        "name": provider.display_name,
                        "error": str(exc),
                    }
                )
        self.last_results = results
        return results

    async def report_rejection(self, event: dict) -> list[dict]:
        results = []
        for provider in self.providers:
            try:
                result = await provider.report_rejection(event)
                outcome = {
                    "provider": provider.provider_id,
                    "instance": provider.instance_name,
                    **result,
                }
            except Exception as exc:
                outcome = {
                    "provider": provider.provider_id,
                    "instance": provider.instance_name,
                    "status": "failed",
                    "reason": str(exc),
                }
                log.exception(
                    "Automation rejection feedback failed for %s",
                    provider.instance_name,
                )

            self.store.save_automation_event(
                torrent_hash=str(event.get("torrent_hash", "")),
                provider=outcome["provider"],
                instance=outcome["instance"],
                event_type="rejected",
                status=str(outcome.get("status", "unknown")),
                detail=str(outcome.get("reason", "")),
            )
            results.append(outcome)

        self.last_results = results
        return results
