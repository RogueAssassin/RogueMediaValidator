from pathlib import Path

import pytest

from app.models import ValidationResult
from app.store import Store


def result():
    return ValidationResult.now(
        torrent_hash="abc",
        torrent_name="Movie",
        category="radarr",
        status="approved",
        reason="Verified media payload",
        video_files=1,
        blocked_files=0,
        largest_video_bytes=1_000_000_000,
    )


def test_store_creates_database_in_writable_directory(tmp_path: Path):
    db_path = tmp_path / "rmv.db"
    store = Store(db_path)
    assert db_path.exists()
    assert store.stats() == {
        "total": 0,
        "approved": 0,
        "blocked": 0,
        "enforced": 0,
    }


def test_dry_run_record_can_be_reprocessed_for_enforcement(tmp_path: Path):
    store = Store(tmp_path / "rmv.db")
    store.save(result(), enforced=False)
    assert store.has("abc")
    assert store.has_enforced("abc") is False

    store.save(result(), enforced=True)
    assert store.has_enforced("abc") is True
    assert store.stats()["enforced"] == 1


def test_store_reports_non_directory_data_path(tmp_path: Path):
    blocker = tmp_path / "data"
    blocker.write_text("not a directory")
    with pytest.raises(RuntimeError, match="cannot be created or accessed"):
        Store(blocker / "rmv.db")
