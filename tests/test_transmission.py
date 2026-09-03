import json

import httpx
import pytest

from app.clients.transmission import TransmissionClient


async def client_with(handler):
    client = TransmissionClient(
        "http://transmission:9091/transmission/rpc",
        "user",
        "pass",
    )
    await client.client.aclose()
    client.client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return client


@pytest.mark.asyncio
async def test_modern_transmission_handles_csrf_and_reports_version():
    calls = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        payload = json.loads(request.content.decode())

        if "X-Transmission-Session-Id" not in request.headers:
            return httpx.Response(
                409,
                headers={"X-Transmission-Session-Id": "session-123"},
                request=request,
            )

        assert request.headers["X-Transmission-Session-Id"] == "session-123"
        assert payload["jsonrpc"] == "2.0"
        if payload["method"] == "session_get":
            return httpx.Response(
                200,
                json={
                    "jsonrpc": "2.0",
                    "result": {
                        "version": "4.1.1",
                        "rpc_version_semver": "6.0.1",
                    },
                    "id": payload["id"],
                },
                request=request,
            )
        raise AssertionError(payload["method"])

    client = await client_with(handler)
    assert await client.version() == "4.1.1"
    assert calls["count"] >= 3
    await client.close()


@pytest.mark.asyncio
async def test_modern_transmission_discovers_labels_and_normalizes_torrents():
    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content.decode())
        if "X-Transmission-Session-Id" not in request.headers:
            return httpx.Response(
                409,
                headers={"X-Transmission-Session-Id": "session-abc"},
                request=request,
            )

        method = payload["method"]
        if method == "session_get":
            return httpx.Response(
                200,
                json={
                    "jsonrpc": "2.0",
                    "result": {"version": "4.1.1"},
                    "id": payload["id"],
                },
                request=request,
            )
        if method == "torrent_get":
            return httpx.Response(
                200,
                json={
                    "jsonrpc": "2.0",
                    "result": {
                        "torrents": [
                            {
                                "hash_string": "abc",
                                "name": "Movie",
                                "labels": ["movies", "4k"],
                                "status": 4,
                                "percent_complete": 0.4,
                            },
                            {
                                "hash_string": "def",
                                "name": "Show",
                                "labels": ["tv"],
                                "status": 6,
                                "percent_complete": 1.0,
                            },
                        ]
                    },
                    "id": payload["id"],
                },
                request=request,
            )
        raise AssertionError(method)

    client = await client_with(handler)
    assert await client.scopes() == ["4k", "movies", "tv"]
    torrents = await client.torrents()
    assert torrents[0]["_scopes"] == ["movies", "4k"]
    assert torrents[0]["state"] == "downloading"
    assert torrents[1]["state"] == "uploading"
    await client.close()


@pytest.mark.asyncio
async def test_legacy_transmission_falls_back_to_bespoke_rpc():
    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content.decode())
        if "X-Transmission-Session-Id" not in request.headers:
            return httpx.Response(
                409,
                headers={"X-Transmission-Session-Id": "legacy-session"},
                request=request,
            )

        if payload.get("method") == "session_get":
            return httpx.Response(
                200,
                json={
                    "jsonrpc": "2.0",
                    "error": {"code": -32601, "message": "Method not found"},
                    "id": payload["id"],
                },
                request=request,
            )
        if payload.get("method") == "session-get":
            return httpx.Response(
                200,
                json={
                    "arguments": {"version": "4.0.6"},
                    "result": "success",
                },
                request=request,
            )
        raise AssertionError(payload)

    client = await client_with(handler)
    assert await client.version() == "4.0.6"
    assert client._protocol == "legacy"
    await client.close()


@pytest.mark.asyncio
async def test_transmission_files_are_normalized_for_validator():
    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content.decode())
        if "X-Transmission-Session-Id" not in request.headers:
            return httpx.Response(
                409,
                headers={"X-Transmission-Session-Id": "session-files"},
                request=request,
            )

        if payload["method"] == "session_get":
            return httpx.Response(
                200,
                json={
                    "jsonrpc": "2.0",
                    "result": {"version": "4.1.1"},
                    "id": payload["id"],
                },
                request=request,
            )
        if payload["method"] == "torrent_get":
            return httpx.Response(
                200,
                json={
                    "jsonrpc": "2.0",
                    "result": {
                        "torrents": [
                            {
                                "files": [
                                    {"name": "Movie.mkv", "length": 2_000_000_000}
                                ]
                            }
                        ]
                    },
                    "id": payload["id"],
                },
                request=request,
            )
        raise AssertionError(payload)

    client = await client_with(handler)
    assert await client.files("abc") == [
        {"name": "Movie.mkv", "size": 2_000_000_000}
    ]
    await client.close()
