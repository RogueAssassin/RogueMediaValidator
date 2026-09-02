from app.config import Settings
from app.service import torrent_actionable, torrent_should_inspect


def settings():
    return Settings(_env_file=None)


def test_paused_radarr_download_is_inspected_and_actionable():
    torrent = {"category": "radarr", "state": "pausedDL"}
    assert torrent_should_inspect(torrent, settings())
    assert torrent_actionable(torrent, settings())


def test_active_download_is_inspected_and_actionable():
    torrent = {"category": "radarr", "state": "downloading"}
    assert torrent_should_inspect(torrent, settings())
    assert torrent_actionable(torrent, settings())


def test_stalled_download_is_inspected_and_actionable():
    torrent = {"category": "sonarr", "state": "stalledDL"}
    assert torrent_should_inspect(torrent, settings())
    assert torrent_actionable(torrent, settings())


def test_seeding_torrent_is_inspected_but_not_actionable():
    torrent = {"category": "sonarr", "state": "uploading"}
    assert torrent_should_inspect(torrent, settings())
    assert not torrent_actionable(torrent, settings())


def test_completed_stopped_upload_is_inspected_but_not_actionable():
    torrent = {"category": "radarr", "state": "stoppedUP"}
    assert torrent_should_inspect(torrent, settings())
    assert not torrent_actionable(torrent, settings())


def test_unmanaged_category_is_never_inspected():
    torrent = {"category": "manual", "state": "pausedDL"}
    assert not torrent_should_inspect(torrent, settings())


def test_inspect_all_states_can_be_disabled():
    cfg = Settings(_env_file=None, qb_inspect_all_states=False)
    torrent = {"category": "radarr", "state": "uploading"}
    assert not torrent_should_inspect(torrent, cfg)
