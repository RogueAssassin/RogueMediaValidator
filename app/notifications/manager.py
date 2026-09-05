import json
import logging

import httpx

from .base import NotificationTarget

log = logging.getLogger("rmv.notifications")


class NotificationManager:
    def __init__(self, targets: list[NotificationTarget], store):
        self.targets = targets
        self.store = store
        self.last_results: list[dict] = []

    @property
    def configured(self) -> bool:
        return bool(self.targets)

    async def close(self):
        for target in self.targets:
            await target.close()

    async def test_all(self) -> list[dict]:
        results = []
        for target in self.targets:
            try:
                data = await target.test()
                results.append({"ok": True, **data})
            except (httpx.HTTPError, RuntimeError, TypeError, ValueError) as exc:
                results.append(
                    {
                        "ok": False,
                        "target": target.target_id,
                        "name": target.display_name,
                        "error": str(exc),
                    }
                )
        self.last_results = results
        return results

    async def emit(self, event_type: str, payload: dict) -> list[dict]:
        results = []
        for target in self.targets:
            if event_type not in target.events:
                continue

            try:
                result = await target.send(event_type, payload)
                outcome = {
                    "target": target.target_id,
                    "name": target.display_name,
                    **result,
                }
            except (httpx.HTTPError, RuntimeError, TypeError, ValueError) as exc:
                outcome = {
                    "target": target.target_id,
                    "name": target.display_name,
                    "status": "failed",
                    "reason": str(exc),
                }
                log.exception("Notification delivery failed for %s", target.display_name)

            self.store.save_notification_event(
                event_type=event_type,
                target=outcome["target"],
                name=outcome["name"],
                status=str(outcome.get("status", "unknown")),
                detail=json.dumps(outcome, sort_keys=True, separators=(",", ":")),
            )
            results.append(outcome)

        self.last_results = results
        return results
