from pathlib import Path

import pytest

from app.config import Settings
from app.models import ValidationResult
from app.store import Store


def result():
    return ValidationResult.now(
        torrent_hash="abc",
        torrent_name="Movie",
        category="movies",
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
        "action_failures": 0,
        "limited_actions": 0,
    }


def test_dry_run_record_can_be_reprocessed_for_enforcement(tmp_path: Path):
    store = Store(tmp_path / "rmv.db")
    fingerprint = "policy-a"
    store.save(result(), policy_fingerprint=fingerprint, enforced=False)
    assert store.has_current("abc", fingerprint)
    assert store.has_enforced_current("abc", fingerprint) is False

    store.save(
        result(),
        policy_fingerprint=fingerprint,
        enforced=True,
        action="resume",
        action_status="success",
    )
    assert store.has_enforced_current("abc", fingerprint) is True
    assert store.stats()["enforced"] == 1


def test_policy_change_requires_revalidation(tmp_path: Path):
    store = Store(tmp_path / "rmv.db")
    store.save(result(), policy_fingerprint="policy-a", enforced=True)

    assert store.has_current("abc", "policy-a")
    assert store.has_enforced_current("abc", "policy-a")
    assert not store.has_current("abc", "policy-b")
    assert not store.has_enforced_current("abc", "policy-b")


def test_action_failure_and_limited_action_are_visible_in_stats(tmp_path: Path):
    store = Store(tmp_path / "rmv.db")
    store.save(
        result(),
        policy_fingerprint="policy-a",
        enforced=False,
        action="resume",
        action_status="failed",
        action_error="torrent client unavailable",
    )
    assert store.stats()["action_failures"] == 1

    store.save(
        ValidationResult.now(
            torrent_hash="def",
            torrent_name="Movie 2",
            category="movies",
            status="blocked",
            reason="Blocked",
            video_files=0,
            blocked_files=1,
            largest_video_bytes=0,
        ),
        policy_fingerprint="policy-a",
        enforced=True,
        action="delete",
        action_status="limited",
        action_error="data cleanup unavailable",
    )
    assert store.stats()["limited_actions"] == 1


def test_store_reports_non_directory_data_path(tmp_path: Path):
    blocker = tmp_path / "data"
    blocker.write_text("not a directory")
    with pytest.raises(RuntimeError, match="cannot be created or accessed"):
        Store(blocker / "rmv.db")


def test_policy_fingerprint_changes_when_validation_policy_changes():
    base = Settings(_env_file=None)
    changed = Settings(_env_file=None, min_video_size_mb=75)
    assert base.policy_fingerprint != changed.policy_fingerprint


def test_bootstrap_scopes_persist_across_store_instances(tmp_path: Path):
    db_path = tmp_path / "rmv.db"
    first = Store(db_path)
    first.set_bootstrap_scopes(["TV", "movies", "tv"], "qbittorrent")

    second = Store(db_path)
    assert second.scope_bootstrap_complete("qbittorrent") is True
    assert second.bootstrap_scopes("qbittorrent") == frozenset({"movies", "tv"})
