from typing import Protocol


class NotificationTarget(Protocol):
    target_id: str
    display_name: str
    events: frozenset[str]

    async def close(self) -> None: ...

    async def test(self) -> dict: ...

    async def send(self, event_type: str, payload: dict) -> dict: ...
