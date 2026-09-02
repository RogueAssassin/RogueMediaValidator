from app.config import Settings
from app.service import torrent_is_eligible


def settings():
    return Settings(_env_file=None)


def test_paused_radarr_download_is_eligible():
    assert torrent_is_eligible(
        {"category": "radarr", "state": "pausedDL"}, settings()
    )


def test_stopped_sonarr_download_is_eligible():
    assert torrent_is_eligible(
        {"category": "sonarr", "state": "stoppedDL"}, settings()
    )


def test_active_download_is_not_eligible():
    assert not torrent_is_eligible(
        {"category": "radarr", "state": "downloading"}, settings()
    )


def test_seeding_torrent_is_not_eligible():
    assert not torrent_is_eligible(
        {"category": "sonarr", "state": "uploading"}, settings()
    )


def test_unmanaged_category_is_not_eligible():
    assert not torrent_is_eligible(
        {"category": "manual", "state": "pausedDL"}, settings()
    )
