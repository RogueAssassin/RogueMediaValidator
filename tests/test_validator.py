from app.config import Settings
from app.validator import validate_payload


def settings():
    return Settings(_env_file=None, min_video_size_mb=50)


def test_valid_mkv_with_subtitle_is_approved():
    r = validate_payload(torrent_hash="a", torrent_name="Movie", category="radarr", files=[
        {"name":"Movie.mkv","size":2_000_000_000},{"name":"Movie.srt","size":42_000}
    ], settings=settings())
    assert r.status == "approved"


def test_executable_is_blocked_even_with_video():
    r = validate_payload(torrent_hash="b", torrent_name="Movie", category="radarr", files=[
        {"name":"Movie.mkv","size":2_000_000_000},{"name":"setup.exe","size":1_000_000}
    ], settings=settings())
    assert r.status == "blocked"
    assert "setup.exe" in r.reason


def test_double_extension_exe_is_blocked():
    r = validate_payload(torrent_hash="c", torrent_name="Movie", category="radarr", files=[
        {"name":"Movie.mkv.exe","size":500_000_000}
    ], settings=settings())
    assert r.status == "blocked"


def test_no_video_is_blocked():
    r = validate_payload(torrent_hash="d", torrent_name="Movie", category="radarr", files=[
        {"name":"poster.jpg","size":500_000}
    ], settings=settings())
    assert r.status == "blocked"
    assert "No approved video" in r.reason


def test_tiny_video_is_blocked():
    r = validate_payload(torrent_hash="e", torrent_name="Movie", category="radarr", files=[
        {"name":"Movie.mkv","size":1024}
    ], settings=settings())
    assert r.status == "blocked"
    assert "minimum size" in r.reason


def test_unknown_extension_fails_closed():
    r = validate_payload(torrent_hash="f", torrent_name="Movie", category="radarr", files=[
        {"name":"Movie.mkv","size":2_000_000_000},{"name":"payload.xyz","size":1000}
    ], settings=settings())
    assert r.status == "blocked"
    assert "Unapproved file type" in r.reason
