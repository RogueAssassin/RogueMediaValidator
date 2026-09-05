import json

from .webhook import WebhookNotificationTarget


SUPPORTED_NOTIFICATION_EVENTS = frozenset(
    {"approved", "rejected", "failed", "limited", "quarantined"}
)


def build_notification_targets(raw: str):
    if not raw.strip():
        return []

    payload = json.loads(raw)
    if not isinstance(payload, list):
        raise TypeError("RMV_NOTIFICATION_TARGETS_JSON must contain a JSON array")

    targets = []
    for index, config in enumerate(payload, start=1):
        if not isinstance(config, dict):
            continue

        target_id = str(config.get("provider", "webhook")).strip().lower()
        if target_id != "webhook":
            raise ValueError(f"Unsupported notification provider: {target_id}")

        name = str(config.get("name") or f"webhook-{index}").strip()
        url = str(config.get("url", "")).strip()
        if not url:
            raise ValueError(f"{name}: url is required")

        configured_events = config.get("events", sorted(SUPPORTED_NOTIFICATION_EVENTS))
        if not isinstance(configured_events, list):
            raise TypeError(f"{name}: events must be a JSON array")

        events = frozenset(
            str(value).strip().lower()
            for value in configured_events
            if str(value).strip().lower() in SUPPORTED_NOTIFICATION_EVENTS
        )
        if not events:
            raise ValueError(f"{name}: at least one supported event is required")

        targets.append(
            WebhookNotificationTarget(
                name=name,
                url=url,
                token=str(config.get("token", "")),
                events=events,
            )
        )
    return targets
