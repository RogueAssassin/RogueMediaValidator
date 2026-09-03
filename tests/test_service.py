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


def test_category_matching_is_case_insensitive():
    cfg = Settings(_env_file=None, qb_categories="TV,Movies")
    assert torrent_in_scope({"category": "tv"}, cfg)
    assert torrent_in_scope({"category": "MOVIES"}, cfg)


def test_inspect_all_states_can_be_disabled():
    cfg = Settings(_env_file=None, qb_categories="tv,movies", qb_inspect_all_states=False)
    torrent = {"category": "tv", "state": "uploading"}
    assert not torrent_should_inspect(torrent, cfg)
