import httpx


class ArrAutomationProvider:
    def __init__(
        self,
        provider_id: str,
        display_name: str,
        instance_name: str,
        base_url: str,
        api_key: str,
    ):
        self.provider_id = provider_id
        self.display_name = display_name
        self.instance_name = instance_name
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        timeout = httpx.Timeout(15.0, connect=5.0)
        transport = httpx.AsyncHTTPTransport(retries=2)
        self.client = httpx.AsyncClient(
            timeout=timeout,
            transport=transport,
            headers={"X-Api-Key": api_key},
            limits=httpx.Limits(max_connections=6, max_keepalive_connections=3),
        )

    async def close(self):
        await self.client.aclose()

    async def test(self) -> dict:
        response = await self.client.get(f"{self.base_url}/api/v3/system/status")
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise TypeError(f"{self.display_name} returned an invalid status response")
        return {
            "provider": self.provider_id,
            "instance": self.instance_name,
            "name": self.display_name,
            "version": str(payload.get("version") or "unknown"),
            "app_name": str(payload.get("appName") or self.display_name),
        }

    async def _queue(self) -> list[dict]:
        response = await self.client.get(
            f"{self.base_url}/api/v3/queue",
            params={"page": 1, "pageSize": 100},
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise TypeError(f"{self.display_name} returned an invalid queue response")
        records = payload.get("records", [])
        if not isinstance(records, list):
            raise TypeError(f"{self.display_name} returned invalid queue records")
        return [item for item in records if isinstance(item, dict)]

    async def report_rejection(self, event: dict) -> dict:
        torrent_hash = str(event.get("torrent_hash", "")).strip().lower()
        if not torrent_hash:
            return {"status": "skipped", "reason": "missing torrent hash"}

        queue_item = next(
            (
                item
                for item in await self._queue()
                if str(item.get("downloadId", "")).strip().lower() == torrent_hash
            ),
            None,
        )
        if queue_item is None:
            return {"status": "not_found", "reason": "downloadId not present in automation queue"}

        queue_id = queue_item.get("id")
        if queue_id is None:
            return {"status": "not_found", "reason": "matched queue item has no id"}

        reason = str(event.get("reason", "Rejected by RogueMediaValidator"))
        response = await self.client.delete(
            f"{self.base_url}/api/v3/queue/{queue_id}",
            params={
                "removeFromClient": "false",
                "blocklist": "true",
                "skipRedownload": "false",
                "changeCategory": "false",
                "message": f"RogueMediaValidator: {reason}"[:250],
            },
        )
        response.raise_for_status()
        return {
            "status": "reported",
            "queue_id": queue_id,
            "blocklist": True,
            "remove_from_client": False,
        }
