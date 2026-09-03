from app.config import Settings
from app.service import torrent_actionable, torrent_in_scope, torrent_should_inspect


def settings():
    return Settings(_env_file=None, qb_categories="tv,movies")


def test_paused_movie_download_is_inspected_and_actionable():
    torrent = {"category": "movies", "state": "pausedDL"}
    assert torrent_should_inspect(torrent, settings())
    assert torrent_actionable(torrent, settings())


def test_active_tv_download_is_inspected_and_actionable():
    torrent = {"category": "tv", "state": "downloading"}
    assert torrent_should_inspect(torrent, settings())
    assert torrent_actionable(torrent, settings())


def test_stalled_tv_download_is_inspected_and_actionable():
    torrent = {"category": "tv", "state": "stalledDL"}
    assert torrent_should_inspect(torrent, settings())
    assert torrent_actionable(torrent, settings())


def test_seeding_torrent_is_inspected_but_not_actionable():
    torrent = {"category": "tv", "state": "uploading"}
    assert torrent_should_inspect(torrent, settings())
    assert not torrent_actionable(torrent, settings())


def test_completed_stopped_upload_is_inspected_but_not_actionable():
    torrent = {"category": "movies", "state": "stoppedUP"}
    assert torrent_should_inspect(torrent, settings())
    assert not torrent_actionable(torrent, settings())


def test_unmanaged_category_is_never_inspected():
    torrent = {"category": "manual", "state": "pausedDL"}
    assert not torrent_should_inspect(torrent, settings())


def test_empty_categories_fail_closed():
    cfg = Settings(_env_file=None, qb_categories="")
    assert not torrent_in_scope({"category": "movies", "state": "pausedDL"}, cfg)


def test_explicit_wildcard_scopes_non_empty_categories():
    cfg = Settings(_env_file=None, qb_categories="*")
    assert torrent_in_scope({"category": "movies"}, cfg)
    assert torrent_in_scope({"category": "manual"}, cfg)
    assert not torrent_in_scope({"category": ""}, cfg)


def test_scope_matching_is_case_insensitive():
    cfg = Settings(_env_file=None, torrent_scopes="TV,Movies")
    assert torrent_in_scope({"_scopes": ["tv"]}, cfg)
    assert torrent_in_scope({"_scopes": ["MOVIES"]}, cfg)


def test_transmission_multi_label_torrent_matches_any_managed_scope():
    cfg = Settings(_env_file=None, torrent_scopes="tv")
    torrent = {"_scopes": ["archive", "TV"], "state": "downloading"}
    assert torrent_in_scope(torrent, cfg)


def test_inspect_all_states_can_be_disabled():
    cfg = Settings(
        _env_file=None,
        qb_categories="tv,movies",
        torrent_inspect_all_states=False,
    )
    torrent = {"category": "tv", "state": "uploading"}
    assert not torrent_should_inspect(torrent, cfg)


def test_first_blank_install_bootstraps_discovered_scopes(tmp_path):
    from app.service import ValidationService
    from app.store import Store

    cfg = Settings(_env_file=None, torrent_scopes="", torrent_auto_bootstrap_scopes=True)
    store = Store(tmp_path / "rmv.db")
    service = ValidationService(cfg, store, client=None, client_name="qbittorrent")
    service.discovered_scopes = ["Movies", "tv", ""]

    service._maybe_bootstrap_scopes()

    assert service.managed_scopes == frozenset({"movies", "tv"})
    assert service.scope_source == "auto_bootstrap"
    assert store.category_bootstrap_complete("qbittorrent") is True
    assert store.bootstrap_categories("qbittorrent") == frozenset({"movies", "tv"})


def test_new_scopes_are_not_auto_added_after_first_bootstrap(tmp_path):
    from app.service import ValidationService
    from app.store import Store

    cfg = Settings(_env_file=None, torrent_scopes="", torrent_auto_bootstrap_scopes=True)
    store = Store(tmp_path / "rmv.db")
    store.set_bootstrap_categories(["movies", "tv"], "transmission")
    service = ValidationService(cfg, store, client=None, client_name="transmission")
    service.discovered_scopes = ["movies", "tv", "manual"]

    service._maybe_bootstrap_scopes()

    assert service.managed_scopes == frozenset({"movies", "tv"})
    assert "manual" not in service.managed_scopes


def test_explicit_environment_scopes_override_bootstrap(tmp_path):
    from app.service import ValidationService
    from app.store import Store

    cfg = Settings(_env_file=None, torrent_scopes="anime")
    store = Store(tmp_path / "rmv.db")
    store.set_bootstrap_categories(["movies", "tv"], "transmission")
    service = ValidationService(cfg, store, client=None, client_name="transmission")

    assert service.managed_scopes == frozenset({"anime"})
    assert service.scope_source == "environment"


def test_auto_bootstrap_can_be_disabled(tmp_path):
    from app.service import ValidationService
    from app.store import Store

    cfg = Settings(_env_file=None, torrent_scopes="", torrent_auto_bootstrap_scopes=False)
    store = Store(tmp_path / "rmv.db")
    service = ValidationService(cfg, store, client=None, client_name="transmission")
    service.discovered_scopes = ["movies", "tv"]

    service._maybe_bootstrap_scopes()

    assert service.managed_scopes == frozenset()
    assert store.category_bootstrap_complete("transmission") is False


def test_provider_bootstrap_scopes_are_isolated(tmp_path):
    from app.store import Store

    store = Store(tmp_path / "rmv.db")
    store.set_bootstrap_categories(["tv"], "qbittorrent")
    store.set_bootstrap_categories(["movies"], "transmission")

    assert store.bootstrap_categories("qbittorrent") == frozenset({"tv"})
    assert store.bootstrap_categories("transmission") == frozenset({"movies"})
