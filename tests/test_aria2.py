import json

import httpx
import pytest

from app.clients.aria2 import Aria2Client


async def client_with(handler):
    client = Aria2Client("http://aria2:6800/jsonrpc", "", "rpc-secret")
    await client.client.aclose()
    client.client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return client


@pytest.mark.asyncio
async def test_aria2_version_scopes_files_and_actions():
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.read().decode())
        method = body["method"]
        params = body.get("params", [])
        calls.append((method, params))
        assert params[0] == "token:rpc-secret"

        if method == "aria2.getVersion":
            result = {"version": "1.37.0"}
        elif method == "aria2.tellActive":
            result = [
                {
                    "gid": "abc",
                    "status": "active",
                    "totalLength": "2000000000",
                    "completedLength": "1000",
                    "dir": "/downloads/movies",
                    "bittorrent": {"info": {"name": "Movie"}},
                }
            ]
        elif method == "aria2.tellWaiting":
            result = [
                {
                    "gid": "def",
                    "status": "paused",
                    "totalLength": "1000000000",
                    "completedLength": "0",
                    "dir": "/downloads/tv",
                    "bittorrent": {"info": {"name": "Show"}},
                }
            ]
        elif method == "aria2.tellStopped":
            result = []
        elif method == "aria2.tellStatus":
            result = {
                "files": [
                    {"path": "/downloads/movies/Movie.mkv", "length": "2000000000"}
                ]
            }
        elif method in {"aria2.unpause", "aria2.remove"}:
            result = params[-1]
        else:
            raise AssertionError(method)

        return httpx.Response(
            200,
            json={"jsonrpc": "2.0", "id": body["id"], "result": result},
            request=request,
        )

    client = await client_with(handler)

    assert await client.version() == "1.37.0"
    assert await client.scopes() == ["/downloads/movies", "/downloads/tv"]

    torrents = await client.torrents()
    assert torrents[0]["name"] == "Movie"
    assert torrents[0]["state"] == "downloading"
    assert torrents[1]["state"] == "stoppeddl"

    assert await client.files("abc") == [
        {"name": "/downloads/movies/Movie.mkv", "size": 2_000_000_000}
    ]

    await client.resume("abc")
    await client.delete("abc", False)

    assert any(method == "aria2.unpause" for method, _ in calls)
    assert any(method == "aria2.remove" for method, _ in calls)
    assert client.supports_delete_data is False
    await client.close()


@pytest.mark.asyncio
async def test_aria2_ignores_non_bittorrent_downloads():
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.read().decode())
        method = body["method"]

        if method == "aria2.tellActive":
            result = [{"gid": "http", "status": "active", "dir": "/downloads"}]
        elif method in {"aria2.tellWaiting", "aria2.tellStopped"}:
            result = []
        else:
            raise AssertionError(method)

        return httpx.Response(
            200,
            json={"jsonrpc": "2.0", "id": body["id"], "result": result},
            request=request,
        )

    client = await client_with(handler)
    assert await client.torrents() == []
    await client.close()
