import json

import httpx
import pytest

from app.automation.arr import ArrAutomationProvider
from app.automation.factory import build_automation_providers, parse_automation_configs
from app.automation.manager import AutomationManager
from app.automation.webhook import WebhookAutomationProvider
from app.store import Store


@pytest.mark.asyncio
async def test_arr_provider_tests_status_and_reports_matching_download_without_client_delete():
    calls = []

    def handler(request: httpx.Request):
        calls.append((request.method, str(request.url)))
        if request.url.path == "/api/v3/system/status":
            assert request.headers["X-Api-Key"] == "secret"
            return httpx.Response(200, json={"version": "6.0.0", "appName": "Radarr"})
        if request.url.path == "/api/v3/queue":
            return httpx.Response(
                200,
                json={
                    "records": [
                        {"id": 42, "downloadId": "ABCDEF", "title": "Movie.Release"}
                    ]
                },
            )
        if request.url.path == "/api/v3/queue/42":
            params = dict(request.url.params)
            assert params["removeFromClient"] == "false"
            assert params["blocklist"] == "true"
            assert params["skipRedownload"] == "false"
            return httpx.Response(200)
        return httpx.Response(404)

    provider = ArrAutomationProvider(
        provider_id="radarr",
        display_name="Radarr",
        instance_name="Movies",
        base_url="http://radarr:7878",
        api_key="secret",
    )
    await provider.client.aclose()
    provider.client = httpx.AsyncClient(transport=httpx.MockTransport(handler))

    status = await provider.test()
    result = await provider.report_rejection(
        {
            "torrent_hash": "abcdef",
            "torrent_name": "Movie.Release",
            "reason": "Blocked executable",
        }
    )

    assert status["version"] == "6.0.0"
    assert result["status"] == "reported"
    assert result["queue_id"] == 42
    assert result["remove_from_client"] is False
    await provider.close()


@pytest.mark.asyncio
async def test_arr_provider_returns_not_found_when_hash_is_not_in_queue():
    def handler(request: httpx.Request):
        if request.url.path == "/api/v3/queue":
            return httpx.Response(200, json={"records": []})
        return httpx.Response(404)

    provider = ArrAutomationProvider(
        provider_id="sonarr",
        display_name="Sonarr",
        instance_name="TV",
        base_url="http://sonarr:8989",
        api_key="secret",
    )
    await provider.client.aclose()
    provider.client = httpx.AsyncClient(transport=httpx.MockTransport(handler))

    result = await provider.report_rejection({"torrent_hash": "missing"})

    assert result["status"] == "not_found"
    await provider.close()


@pytest.mark.asyncio
async def test_generic_webhook_receives_provider_neutral_rejection_event():
    received = {}

    def handler(request: httpx.Request):
        received["auth"] = request.headers.get("Authorization")
        received["payload"] = json.loads(request.content)
        return httpx.Response(202)

    provider = WebhookAutomationProvider(
        instance_name="Custom automation",
        url="http://automation.local/rmv",
        token="token-value",
    )
    await provider.client.aclose()
    provider.client = httpx.AsyncClient(transport=httpx.MockTransport(handler))

    result = await provider.report_rejection(
        {
            "torrent_hash": "abc",
            "torrent_name": "Unsafe.Release",
            "reason": "Blocked executable",
            "provider": "qbittorrent",
        }
    )

    assert result == {"status": "reported", "http_status": 202}
    assert received["auth"] == "Bearer token-value"
    assert received["payload"]["event"] == "rmv.rejected"
    assert received["payload"]["torrent_hash"] == "abc"
    await provider.close()


def test_factory_supports_multiple_instances_and_universal_webhook():
    raw = json.dumps(
        [
            {
                "provider": "radarr",
                "name": "Movies",
                "url": "http://radarr:7878",
                "api_key": "a",
            },
            {
                "provider": "sonarr",
                "name": "Anime TV",
                "url": "http://sonarr-anime:8989",
                "api_key": "b",
            },
            {
                "provider": "webhook",
                "name": "Custom",
                "url": "http://custom/rmv",
                "token": "c",
            },
        ]
    )

    providers = build_automation_providers(raw)

    assert [p.provider_id for p in providers] == ["radarr", "sonarr", "webhook"]
    assert [p.instance_name for p in providers] == ["Movies", "Anime TV", "Custom"]


def test_factory_rejects_invalid_configuration():
    with pytest.raises(ValueError, match="JSON array"):
        parse_automation_configs('{"provider":"radarr"}')

    with pytest.raises(ValueError, match="Unsupported automation provider"):
        build_automation_providers('[{"provider":"unknown","url":"http://example"}]')


class GoodProvider:
    provider_id = "webhook"
    display_name = "Good"
    instance_name = "good"

    async def close(self):
        return None

    async def test(self):
        return {"provider": self.provider_id, "instance": self.instance_name, "name": self.display_name, "version": "1"}

    async def report_rejection(self, event):
        return {"status": "reported"}


class FailedProvider:
    provider_id = "webhook"
    display_name = "Failed"
    instance_name = "failed"

    async def close(self):
        return None

    async def test(self):
        raise RuntimeError("offline")

    async def report_rejection(self, event):
        raise RuntimeError("offline")


@pytest.mark.asyncio
async def test_manager_isolates_provider_failure_and_audits_each_instance(tmp_path):
    store = Store(tmp_path / "rmv.db")
    manager = AutomationManager([GoodProvider(), FailedProvider()], store)

    results = await manager.report_rejection({"torrent_hash": "abc"})

    assert results[0]["status"] == "reported"
    assert results[1]["status"] == "failed"
    events = store.automation_events(10)
    assert len(events) == 2
    assert {event["status"] for event in events} == {"reported", "failed"}
    assert store.automation_stats()["failed"] == 1
