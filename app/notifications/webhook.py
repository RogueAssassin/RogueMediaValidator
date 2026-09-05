import httpx


class WebhookNotificationTarget:
    target_id = "webhook"

    def __init__(
        self,
        *,
        name: str,
        url: str,
        token: str = "",
        events: frozenset[str] = frozenset(),
    ):
        self.display_name = name
        self.url = url
        self.token = token
        self.events = events
        timeout = httpx.Timeout(15.0, connect=5.0)
        transport = httpx.AsyncHTTPTransport(retries=2)
        self.client = httpx.AsyncClient(
            timeout=timeout,
            transport=transport,
            limits=httpx.Limits(max_connections=6, max_keepalive_connections=3),
        )

    async def close(self):
        await self.client.aclose()

    async def test(self) -> dict:
        return {
            "target": self.target_id,
            "name": self.display_name,
            "configured": bool(self.url),
            "events": sorted(self.events),
        }

    async def send(self, event_type: str, payload: dict) -> dict:
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        response = await self.client.post(
            self.url,
            json={"event": f"rmv.{event_type}", **payload},
            headers=headers,
        )
        response.raise_for_status()
        return {"status": "sent", "http_status": response.status_code}
