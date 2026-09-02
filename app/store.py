import sqlite3
from pathlib import Path

from .models import ValidationResult


class Store:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        with self._connect() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS validations (
                    torrent_hash TEXT PRIMARY KEY,
                    torrent_name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    status TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    video_files INTEGER NOT NULL,
                    blocked_files INTEGER NOT NULL,
                    largest_video_bytes INTEGER NOT NULL,
                    checked_at TEXT NOT NULL
                )
            """)

    def _connect(self):
        return sqlite3.connect(self.path)

    def save(self, result: ValidationResult):
        data = result.as_dict()
        with self._connect() as db:
            db.execute("""
                INSERT OR REPLACE INTO validations
                (torrent_hash,torrent_name,category,status,reason,video_files,blocked_files,largest_video_bytes,checked_at)
                VALUES (:torrent_hash,:torrent_name,:category,:status,:reason,:video_files,:blocked_files,:largest_video_bytes,:checked_at)
            """, data)

    def has(self, torrent_hash: str) -> bool:
        with self._connect() as db:
            return db.execute(
                "SELECT 1 FROM validations WHERE torrent_hash=?", (torrent_hash,)
            ).fetchone() is not None

    def recent(self, limit: int = 50) -> list[dict]:
        with self._connect() as db:
            db.row_factory = sqlite3.Row
            rows = db.execute(
                "SELECT * FROM validations ORDER BY checked_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]

    def stats(self) -> dict:
        with self._connect() as db:
            rows = db.execute(
                "SELECT status, COUNT(*) FROM validations GROUP BY status"
            ).fetchall()
        counts = {k: v for k, v in rows}
        return {
            "total": sum(counts.values()),
            "approved": counts.get("approved", 0),
            "blocked": counts.get("blocked", 0),
        }
