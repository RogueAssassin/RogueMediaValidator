import pytest

from app.config import Settings
from app.service import (
    ValidationService,
    torrent_actionable,
    torrent_in_scope,
    torrent_should_inspect,
)
from app.store import Store


def settings():
    return Settings(_env_file=None, torrent_scopes="tv,movies")


def test_paused_movie_download_is_inspected_and_actionable():
    torrent = {"_scopes": ["movies"], "state": "pausedDL"}
    assert torrent_should_inspect(torrent, settings())
    assert torrent_actionable(torrent, settings())


def test_active_tv_download_is_inspected_and_actionable():
    torrent = {"_scopes": ["tv"], "state": "downloading"}
    assert torrent_should_inspect(torrent, settings())
    assert torrent_actionable(torrent, settings())


def test_seeding_torrent_is_inspected_but_not_actionable():
    torrent = {"_scopes": ["tv"], "state": "uploading"}
    assert torrent_should_inspect(torrent, settings())
    assert not torrent_actionable(torrent, settings())


def test_unmanaged_scope_is_never_inspected():
    torrent = {"_scopes": ["manual"], "state": "pausedDL"}
    assert not torrent_should_inspect(torrent, settings())


def test_empty_scopes_fail_closed():
    cfg = Settings(_env_file=None, torrent_scopes="")
    assert not torrent_in_scope({"_scopes": ["movies"], "state": "pausedDL"}, cfg)


def test_explicit_wildcard_scopes_non_empty_scope():
    cfg = Settings(_env_file=None, torrent_scopes="*")
    assert torrent_in_scope({"_scopes": ["movies"]}, cfg)
    assert torrent_in_scope({"_scopes": ["manual"]}, cfg)
    assert not torrent_in_scope({"_scopes": []}, cfg)


def test_scope_matching_is_case_insensitive():
    cfg = Settings(_env_file=None, torrent_scopes="TV,Movies")
    assert torrent_in_scope({"_scopes": ["tv"]}, cfg)
    assert torrent_in_scope({"_scopes": ["MOVIES"]}, cfg)


def test_multi_scope_torrent_matches_any_managed_scope():
    cfg = Settings(_env_file=None, torrent_scopes="tv")
    torrent = {"_scopes": ["archive", "TV"], "state": "downloading"}
    assert torrent_in_scope(torrent, cfg)


def test_inspect_all_states_can_be_disabled():
    cfg = Settings(
        _env_file=None,
        torrent_scopes="tv,movies",
        torrent_inspect_all_states=False,
    )
    torrent = {"_scopes": ["tv"], "state": "uploading"}
    assert not torrent_should_inspect(torrent, cfg)


def test_first_blank_install_bootstraps_discovered_scopes(tmp_path):
    cfg = Settings(_env_file=None, torrent_scopes="", torrent_auto_bootstrap_scopes=True)
    store = Store(tmp_path / "rmv.db")
    service = ValidationService(cfg, store, client=None, client_name="qbittorrent")
    service.discovered_scopes = ["Movies", "tv", ""]

    service._maybe_bootstrap_scopes()

    assert service.managed_scopes == frozenset({"movies", "tv"})
    assert service.scope_source == "auto_bootstrap"
    assert store.scope_bootstrap_complete("qbittorrent") is True
    assert store.bootstrap_scopes("qbittorrent") == frozenset({"movies", "tv"})


def test_new_scopes_are_not_auto_added_after_first_bootstrap(tmp_path):
    cfg = Settings(_env_file=None, torrent_scopes="", torrent_auto_bootstrap_scopes=True)
    store = Store(tmp_path / "rmv.db")
    store.set_bootstrap_scopes(["movies", "tv"], "transmission")
    service = ValidationService(cfg, store, client=None, client_name="transmission")
    service.discovered_scopes = ["movies", "tv", "manual"]

    service._maybe_bootstrap_scopes()

    assert service.managed_scopes == frozenset({"movies", "tv"})
    assert "manual" not in service.managed_scopes


def test_explicit_environment_scopes_override_bootstrap(tmp_path):
    cfg = Settings(_env_file=None, torrent_scopes="anime")
    store = Store(tmp_path / "rmv.db")
    store.set_bootstrap_scopes(["movies", "tv"], "transmission")
    service = ValidationService(cfg, store, client=None, client_name="transmission")

    assert service.managed_scopes == frozenset({"anime"})
    assert service.scope_source == "environment"


def test_ui_managed_scopes_override_bootstrap_and_persist(tmp_path):
    cfg = Settings(_env_file=None, torrent_scopes="", torrent_auto_bootstrap_scopes=True)
    store = Store(tmp_path / "rmv.db")
    store.set_bootstrap_scopes(["movies", "tv"], "transmission")
    service = ValidationService(cfg, store, client=None, client_name="transmission")

    service.set_managed_scopes(["TV"])

    assert service.managed_scopes == frozenset({"tv"})
    assert service.scope_source == "ui"

    reloaded = ValidationService(cfg, Store(tmp_path / "rmv.db"), client=None, client_name="transmission")
    assert reloaded.managed_scopes == frozenset({"tv"})
    assert reloaded.scope_source == "ui"


def test_empty_ui_scope_selection_stays_fail_closed(tmp_path):
    cfg = Settings(_env_file=None, torrent_scopes="", torrent_auto_bootstrap_scopes=True)
    store = Store(tmp_path / "rmv.db")
    service = ValidationService(cfg, store, client=None, client_name="qbittorrent")

    service.set_managed_scopes([])
    service.discovered_scopes = ["movies", "tv"]
    service._maybe_bootstrap_scopes()

    assert service.managed_scopes == frozenset()
    assert service.scope_source == "ui"
    assert store.scope_bootstrap_complete("qbittorrent") is False


def test_environment_scopes_cannot_be_overridden_by_ui(tmp_path):
    cfg = Settings(_env_file=None, torrent_scopes="movies")
    store = Store(tmp_path / "rmv.db")
    service = ValidationService(cfg, store, client=None, client_name="qbittorrent")

    with pytest.raises(ValueError, match="controlled by RMV_TORRENT_SCOPES"):
        service.set_managed_scopes(["tv"])


def test_auto_bootstrap_can_be_disabled(tmp_path):
    cfg = Settings(_env_file=None, torrent_scopes="", torrent_auto_bootstrap_scopes=False)
    store = Store(tmp_path / "rmv.db")
    service = ValidationService(cfg, store, client=None, client_name="transmission")
    service.discovered_scopes = ["movies", "tv"]

    service._maybe_bootstrap_scopes()

    assert service.managed_scopes == frozenset()
    assert store.scope_bootstrap_complete("transmission") is False


def test_provider_bootstrap_scopes_are_isolated(tmp_path):
    store = Store(tmp_path / "rmv.db")
    store.set_bootstrap_scopes(["tv"], "qbittorrent")
    store.set_bootstrap_scopes(["movies"], "transmission")

    assert store.bootstrap_scopes("qbittorrent") == frozenset({"tv"})
    assert store.bootstrap_scopes("transmission") == frozenset({"movies"})


class LimitedDeleteClient:
    provider_id = "rtorrent"
    display_name = "rTorrent / ruTorrent"
    scope_name = "labels / download paths"
    supports_delete_data = False

    def __init__(self):
        self.deleted = []

    async def close(self):
        return None

    async def version(self):
        return "0.9.8"

    async def scopes(self):
        return ["tv"]

    async def torrents(self):
        return [
            {
                "hash": "bad",
                "name": "Unsafe.exe",
                "_scopes": ["tv"],
                "state": "stoppeddl",
            }
        ]

    async def files(self, torrent_hash):
        return [{"name": "Unsafe.exe", "size": 1000}]

    async def resume(self, torrent_hash):
        raise AssertionError("blocked torrent should not resume")

    async def delete(self, torrent_hash, delete_files):
        self.deleted.append((torrent_hash, delete_files))


@pytest.mark.asyncio
async def test_provider_without_data_delete_records_limited_action(tmp_path):
    cfg = Settings(
        _env_file=None,
        torrent_scopes="tv",
        dry_run=False,
        delete_rejected_data=True,
    )
    store = Store(tmp_path / "rmv.db")
    client = LimitedDeleteClient()
    service = ValidationService(cfg, store, client, "rtorrent")

    await service.run_once()

    assert client.deleted == [("bad", False)]
    row = store.recent(1)[0]
    assert row["enforced"] == 1
    assert row["action"] == "delete"
    assert row["action_status"] == "limited"
    assert "cannot delete local payload data" in row["action_error"]


class QuarantineClient:
    provider_id = "qbittorrent"
    display_name = "qBittorrent"
    scope_name = "categories"
    supports_delete_data = True

    def __init__(self):
        self.paused = []
        self.deleted = []

    async def close(self):
        return None

    async def version(self):
        return "5.2.3"

    async def scopes(self):
        return ["tv"]

    async def torrents(self):
        return [{
            "hash": "quarantine-me",
            "name": "Unsafe release.exe",
            "_scopes": ["tv"],
            "state": "downloading",
        }]

    async def files(self, torrent_hash):
        return [{"name": "Unsafe release.exe", "size": 1000}]

    async def pause(self, torrent_hash):
        self.paused.append(torrent_hash)

    async def resume(self, torrent_hash):
        raise AssertionError("blocked torrent should not resume")

    async def delete(self, torrent_hash, delete_files):
        self.deleted.append((torrent_hash, delete_files))


@pytest.mark.asyncio
async def test_quarantine_holds_rejected_torrent_instead_of_deleting(tmp_path):
    cfg = Settings(
        _env_file=None,
        torrent_scopes="tv",
        dry_run=False,
        quarantine_rejected=True,
        remove_rejected=True,
        delete_rejected_data=True,
    )
    store = Store(tmp_path / "rmv.db")
    client = QuarantineClient()
    service = ValidationService(cfg, store, client, "qbittorrent")

    await service.run_once()

    assert client.paused == ["quarantine-me"]
    assert client.deleted == []
    row = store.recent(1)[0]
    assert row["enforced"] == 1
    assert row["action"] == "quarantine"
    assert row["action_status"] == "held"
    held = store.quarantine_recent(1)[0]
    assert held["torrent_hash"] == "quarantine-me"
    assert held["state"] == "held"


@pytest.mark.asyncio
async def test_quarantine_is_opt_in_and_existing_delete_path_remains_default(tmp_path):
    cfg = Settings(
        _env_file=None,
        torrent_scopes="tv",
        dry_run=False,
        quarantine_rejected=False,
        remove_rejected=True,
        delete_rejected_data=True,
    )
    store = Store(tmp_path / "rmv.db")
    client = QuarantineClient()
    service = ValidationService(cfg, store, client, "qbittorrent")

    await service.run_once()

    assert client.paused == []
    assert client.deleted == [("quarantine-me", True)]
    assert store.quarantine_count() == 0
