import httpx
import pytest

from app.clients.deluge import DelugeClient


async def client_with(handler):
    client = DelugeClient("http://deluge:8112", "", "deluge-pass")
    await client.client.aclose()
    client.client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return client


@pytest.mark.asyncio
async def test_deluge_version_scope_files_and_delete():
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        payload = request.read()
        import json

        body = json.loads(payload.decode())
        method = body["method"]
        params = body.get("params", [])
        calls.append((method, params))

        if method == "auth.login":
            result = True
        elif method == "web.connected":
            result = True
        elif method == "core.get_version":
            result = "2.2.0"
        elif method == "core.get_torrents_status":
            result = {
                "abc": {
                    "name": "Movie",
                    "state": "Downloading",
                    "progress": 25.0,
                    "label": "movies",
                    "download_location": "/downloads/movies",
                },
                "def": {
                    "name": "Show",
                    "state": "Seeding",
                    "progress": 100.0,
                    "label": "",
                    "download_location": "/downloads/tv",
                },
            }
        elif method == "core.get_torrent_status":
            result = {
                "files": [
                    {"path": "Movie.mkv", "size": 2_000_000_000},
                    {"path": "Movie.srt", "size": 42_000},
                ]
            }
        elif method == "core.remove_torrent":
            result = True
        elif method == "core.resume_torrent":
            result = None
        else:
            raise AssertionError(method)

        return httpx.Response(
            200,
            json={"id": body["id"], "result": result, "error": None},
            request=request,
        )

    client = await client_with(handler)

    assert await client.version() == "2.2.0"
    assert await client.scopes() == ["/downloads/tv", "movies"]

    torrents = await client.torrents()
    assert torrents[0]["_scopes"] == ["movies"]
    assert torrents[0]["state"] == "downloading"
    assert torrents[1]["_scopes"] == ["/downloads/tv"]
    assert torrents[1]["state"] == "uploading"

    assert await client.files("abc") == [
        {"name": "Movie.mkv", "size": 2_000_000_000},
        {"name": "Movie.srt", "size": 42_000},
    ]

    await client.resume("abc")
    await client.delete("abc", True)

    assert ("core.resume_torrent", ["abc"]) in calls
    assert ("core.remove_torrent", ["abc", True]) in calls
    assert client.supports_delete_data is True
    await client.close()


@pytest.mark.asyncio
async def test_deluge_connects_first_configured_daemon_when_needed():
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        import json

        body = json.loads(request.read().decode())
        method = body["method"]
        calls.append(method)

        if method == "auth.login":
            result = True
        elif method == "web.connected":
            result = calls.count("web.connected") > 1
        elif method == "web.get_hosts":
            result = [["host-id", "127.0.0.1", 58846, "localclient"]]
        elif method == "web.connect":
            result = ["core.get_version"]
        elif method == "core.get_version":
            result = "2.2.0"
        else:
            raise AssertionError(method)

        return httpx.Response(
            200,
            json={"id": body["id"], "result": result, "error": None},
            request=request,
        )

    client = await client_with(handler)
    assert await client.version() == "2.2.0"
    assert "web.get_hosts" in calls
    assert "web.connect" in calls
    await client.close()
