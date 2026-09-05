from typing import Protocol


class AutomationProvider(Protocol):
    provider_id: str
    display_name: str
    instance_name: str

    async def close(self) -> None: ...

    async def test(self) -> dict: ...

    async def report_rejection(self, event: dict) -> dict: ...
