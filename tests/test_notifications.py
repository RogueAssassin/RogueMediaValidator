import json

import httpx
import pytest

from app.notifications.factory import build_notification_targets
from app.notifications.manager import NotificationManager
from app.notifications.webhook import WebhookNotificationTarget
from app.store import Store


@pytest.mark.asyncio
async def test_webhook_notification_sends_structured_event_and_bearer_token():
    received = {}

    def handler(request: httpx.Request):
        received["auth"] = request.headers.get("Authorization")
        received["payload"] = json.loads(request.content)
        return httpx.Response(202)

    target = WebhookNotificationTarget(
        name="Operations",
        url="http://notify.local/rmv",
        token="secret",
        events=frozenset({"rejected"}),
    )
    await target.client.aclose()
    target.client = httpx.AsyncClient(transport=httpx.MockTransport(handler))

    result = await target.send(
        "rejected",
        {
            "torrent_hash": "abc",
            "torrent_name": "Unsafe.Release",
            "reason": "Blocked executable",
        },
    )

    assert result == {"status": "sent", "http_status": 202}
    assert received["auth"] == "Bearer secret"
    assert received["payload"]["event"] == "rmv.rejected"
    assert received["payload"]["torrent_hash"] == "abc"
    await target.close()


def test_notification_factory_filters_supported_events():
    raw = json.dumps(
        [
            {
                "provider": "webhook",
                "name": "Ops",
                "url": "http://notify/rmv",
                "events": ["approved", "rejected", "unknown"],
            }
        ]
    )

    targets = build_notification_targets(raw)

    assert len(targets) == 1
    assert targets[0].events == frozenset({"approved", "rejected"})


def test_notification_factory_rejects_invalid_shapes():
    with pytest.raises(TypeError, match="JSON array"):
        build_notification_targets('{"provider":"webhook"}')

    with pytest.raises(ValueError, match="Unsupported notification provider"):
        build_notification_targets(
            '[{"provider":"email","name":"mail","url":"http://example"}]'
        )


class GoodTarget:
    target_id = "webhook"
    display_name = "good"
    events = frozenset({"rejected"})

    async def close(self):
        return None

    async def test(self):
        return {
            "target": self.target_id,
            "name": self.display_name,
            "configured": True,
            "events": ["rejected"],
            "http_status": 200,
        }

    async def send(self, event_type, payload):
        return {"status": "sent"}


class FailedTarget:
    target_id = "webhook"
    display_name = "failed"
    events = frozenset({"rejected"})

    async def close(self):
        return None

    async def test(self):
        raise RuntimeError("offline")

    async def send(self, event_type, payload):
        raise RuntimeError("offline")


@pytest.mark.asyncio
async def test_notification_manager_isolates_failures_and_audits_results(tmp_path):
    store = Store(tmp_path / "rmv.db")
    manager = NotificationManager([GoodTarget(), FailedTarget()], store)

    results = await manager.emit("rejected", {"torrent_hash": "abc"})

    assert results[0]["status"] == "sent"
    assert results[1]["status"] == "failed"
    events = store.notification_events(10)
    assert len(events) == 2
    assert {item["status"] for item in events} == {"sent", "failed"}
    assert store.notification_stats() == {"total": 2, "sent": 1, "failed": 1}


@pytest.mark.asyncio
async def test_notification_manager_skips_unsubscribed_events(tmp_path):
    store = Store(tmp_path / "rmv.db")
    manager = NotificationManager([GoodTarget()], store)

    results = await manager.emit("approved", {"torrent_hash": "abc"})

    assert results == []
    assert store.notification_events(10) == []


@pytest.mark.asyncio
async def test_webhook_notification_test_posts_rmv_test_event():
    received = {}

    def handler(request: httpx.Request):
        received["payload"] = json.loads(request.content)
        return httpx.Response(204)

    target = WebhookNotificationTarget(
        name="Ops",
        url="http://notify.local/rmv",
        events=frozenset({"rejected"}),
    )
    await target.client.aclose()
    target.client = httpx.AsyncClient(transport=httpx.MockTransport(handler))

    result = await target.test()

    assert result["http_status"] == 204
    assert received["payload"]["event"] == "rmv.test"
    await target.close()
