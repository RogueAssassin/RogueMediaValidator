# ruff: noqa: I001
from json import loads

from .arr import ArrAutomationProvider
from .webhook import WebhookAutomationProvider



def parse_automation_configs(raw: str) -> list[dict]:
    if not raw.strip():
        return []
    payload = loads(raw)
    if not isinstance(payload, list):
        raise TypeError("RMV_AUTOMATION_PROVIDERS_JSON must contain a JSON array")
    return [item for item in payload if isinstance(item, dict)]


def build_automation_providers(raw: str):
    providers = []
    for index, config in enumerate(parse_automation_configs(raw), start=1):
        provider_id = str(config.get("provider", "")).strip().lower()
        instance_name = str(config.get("name") or f"{provider_id}-{index}").strip()

        if provider_id in {"radarr", "sonarr"}:
            url = str(config.get("url", "")).strip()
            api_key = str(config.get("api_key", "")).strip()
            if not url or not api_key:
                raise ValueError(f"{instance_name}: url and api_key are required")
            providers.append(
                ArrAutomationProvider(
                    provider_id=provider_id,
                    display_name="Radarr" if provider_id == "radarr" else "Sonarr",
                    instance_name=instance_name,
                    base_url=url,
                    api_key=api_key,
                )
            )
        elif provider_id == "webhook":
            url = str(config.get("url", "")).strip()
            if not url:
                raise ValueError(f"{instance_name}: url is required")
            providers.append(
                WebhookAutomationProvider(
                    instance_name=instance_name,
                    url=url,
                    token=str(config.get("token", "")),
                )
            )
        else:
            raise ValueError(f"Unsupported automation provider: {provider_id or '(blank)'}")
    return providers
