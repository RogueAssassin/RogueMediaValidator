import importlib
import sys

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def web(tmp_path, monkeypatch):
    from app.config import get_settings

    monkeypatch.setenv("RMV_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("RMV_ADMIN_USERNAME", "operator")
    monkeypatch.setenv("RMV_ADMIN_PASSWORD", "test-password")
    get_settings.cache_clear()
    sys.modules.pop("app.main", None)
    main = importlib.import_module("app.main")
    main.store.quarantine_hold(
        torrent_hash="abc123",
        torrent_name="Bad <Release>",
        provider="qbittorrent",
        scopes="movies",
        reason="Blocked file type detected: setup.exe",
        at="2026-11-27T01:02:03+00:00",
    )
    yield main, TestClient(main.app)
    get_settings.cache_clear()
    sys.modules.pop("app.main", None)


AUTH = ("operator", "test-password")
DISMISS = "/api/admin/quarantine/abc123/dismiss"


def test_quarantine_page_lists_held_items_escaped(web):
    _, client = web
    response = client.get("/quarantine")
    assert response.status_code == 200
    assert "1 item in quarantine" in response.text
    assert "Bad &lt;Release&gt;" in response.text
    assert "Bad <Release>" not in response.text


def test_dismiss_requires_admin_and_clears_the_item(web):
    main, client = web
    assert client.post(DISMISS).status_code == 401
    assert main.store.quarantine_count() == 1
    assert client.post(DISMISS, auth=AUTH).status_code == 200
    assert main.store.quarantine_count() == 0
    assert client.post(DISMISS, auth=AUTH).status_code == 404
    assert "Nothing is waiting for review" in client.get("/quarantine").text


def test_cross_site_writes_are_rejected(web):
    main, client = web
    response = client.post(DISMISS, auth=AUTH, headers={"Sec-Fetch-Site": "cross-site"})
    assert response.status_code == 403
    assert main.store.quarantine_count() == 1
    assert response.headers["X-Frame-Options"] == "DENY"
