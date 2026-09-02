import httpx
import pytest

from app.qbittorrent import QBittorrentClient


@pytest.mark.asyncio
async def test_login_accepts_204_no_content():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v2/auth/login"
        return httpx.Response(204, request=request)

    client = QBittorrentClient("http://qbittorrent:7800", "user", "pass")
    await client.client.aclose()
    client.client = httpx.AsyncClient(transport=httpx.MockTransport(handler))

    await client.login()

    assert client._logged_in is True
    await client.close()


@pytest.mark.asyncio
async def test_login_accepts_standard_ok_body():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="Ok.", request=request)

    client = QBittorrentClient("http://qbittorrent:7800", "user", "pass")
    await client.client.aclose()
    client.client = httpx.AsyncClient(transport=httpx.MockTransport(handler))

    await client.login()

    assert client._logged_in is True
    await client.close()


@pytest.mark.asyncio
async def test_login_rejects_explicit_failure_body():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="Fails.", request=request)

    client = QBittorrentClient("http://qbittorrent:7800", "user", "pass")
    await client.client.aclose()
    client.client = httpx.AsyncClient(transport=httpx.MockTransport(handler))

    with pytest.raises(RuntimeError, match="authentication failed"):
        await client.login()

    assert client._logged_in is False
    await client.close()
