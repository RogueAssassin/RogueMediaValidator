import httpx
import pytest

from app.clients.qbittorrent import QBittorrentClient


async def client_with(handler):
    client = QBittorrentClient("http://qbittorrent:7800", "user", "pass")
    await client.client.aclose()
    client.client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return client


@pytest.mark.asyncio
async def test_login_accepts_204_no_content():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(204, request=request)

    client = await client_with(handler)
    await client.login()
    assert client._logged_in is True
    await client.close()


@pytest.mark.asyncio
async def test_login_accepts_standard_ok_body():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="Ok.", request=request)

    client = await client_with(handler)
    await client.login()
    assert client._logged_in is True
    await client.close()


@pytest.mark.asyncio
async def test_login_rejects_explicit_failure_body():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="Fails.", request=request)

    client = await client_with(handler)
    with pytest.raises(RuntimeError, match="authentication failed"):
        await client.login()
    assert client._logged_in is False
    await client.close()


@pytest.mark.asyncio
async def test_expired_session_reauthenticates_once():
    calls = {"login": 0, "torrents": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/v2/auth/login":
            calls["login"] += 1
            return httpx.Response(204, request=request)
        if request.url.path == "/api/v2/torrents/info":
            calls["torrents"] += 1
            if calls["torrents"] == 1:
                return httpx.Response(403, request=request)
            return httpx.Response(200, json=[], request=request)
        raise AssertionError(request.url.path)

    client = await client_with(handler)
    assert await client.torrents() == []
    assert calls == {"login": 2, "torrents": 2}
    await client.close()


@pytest.mark.asyncio
async def test_categories_are_discovered_from_qbittorrent():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/v2/auth/login":
            return httpx.Response(200, text="Ok.", request=request)
        if request.url.path == "/api/v2/torrents/categories":
            return httpx.Response(
                200,
                json={
                    "movies": {"savePath": "/downloads/movies"},
                    "tv": {"savePath": "/downloads/tv"},
                },
                request=request,
            )
        raise AssertionError(request.url.path)

    client = await client_with(handler)
    assert await client.categories() == ["movies", "tv"]
    await client.close()
