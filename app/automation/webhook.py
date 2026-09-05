import httpx


class WebhookAutomationProvider:
    provider_id = "webhook"
    display_name = "Generic Webhook"

    def __init__(
        self,
        instance_name: str,
        url: str,
        token: str = "",
    ):
        self.instance_name = instance_name
        self.url = url
        self.token = token
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
            "provider": self.provider_id,
            "instance": self.instance_name,
            "name": self.display_name,
            "version": "webhook",
            "configured": bool(self.url),
        }

    async def report_rejection(self, event: dict) -> dict:
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        response = await self.client.post(
            self.url,
            json={"event": "rmv.rejected", **event},
            headers=headers,
        )
        response.raise_for_status()
        return {"status": "reported", "http_status": response.status_code}
