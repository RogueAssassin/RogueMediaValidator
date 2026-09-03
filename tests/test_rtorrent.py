from xmlrpc.client import dumps, loads

import httpx
import pytest

from app.clients.rtorrent import RTorrentClient


def xml_response(result, request):
    body = dumps((result,), methodresponse=True, allow_none=True)
    return httpx.Response(
        200,
        content=body.encode(),
        headers={"Content-Type": "text/xml"},
        request=request,
    )


async def client_with(handler):
    client = RTorrentClient("http://rutorrent/RPC2", "user", "pass")
    await client.client.aclose()
    client.client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return client


@pytest.mark.asyncio
async def test_rtorrent_version_scopes_files_and_actions():
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        params, method = loads(request.read())
        calls.append((method, params))

        if method == "system.client_version":
            return xml_response("0.9.8", request)
        if method == "d.multicall2":
            return xml_response(
                [
                    ["ABC", "Movie", "movies", "/downloads/movies", 1, 0, 0],
                    ["DEF", "Show", "", "/downloads/tv", 0, 1, 0],
                ],
                request,
            )
        if method == "f.multicall":
            return xml_response(
                [["Movie.mkv", 2_000_000_000], ["Movie.srt", 42_000]],
                request,
            )
        if method in {"d.start", "d.erase"}:
            return xml_response(0, request)
        raise AssertionError(method)

    client = await client_with(handler)

    assert await client.version() == "0.9.8"
    assert await client.scopes() == ["/downloads/tv", "movies"]

    torrents = await client.torrents()
    assert torrents[0]["_scopes"] == ["movies"]
    assert torrents[0]["state"] == "downloading"
    assert torrents[1]["_scopes"] == ["/downloads/tv"]
    assert torrents[1]["state"] == "stoppedup"

    assert await client.files("ABC") == [
        {"name": "Movie.mkv", "size": 2_000_000_000},
        {"name": "Movie.srt", "size": 42_000},
    ]

    await client.resume("ABC")
    await client.delete("ABC", False)

    assert any(method == "d.start" for method, _ in calls)
    assert any(method == "d.erase" for method, _ in calls)
    assert client.supports_delete_data is False
    await client.close()
