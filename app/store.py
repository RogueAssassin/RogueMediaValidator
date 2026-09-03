import sqlite3
from pathlib import Path

from .models import ValidationResult


class Store:
    def __init__(self, path: Path):
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise RuntimeError(
                f"RMV data directory cannot be created or accessed: {path.parent}. "
                "Check the container volume ownership/permissions."
            ) from exc

        if not path.parent.is_dir():
            raise RuntimeError(f"RMV data path is not a directory: {path.parent}")

        self.path = path
        try:
            with self._connect() as db:
                db.execute("PRAGMA journal_mode=WAL")
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
                        checked_at TEXT NOT NULL,
                        enforced INTEGER NOT NULL DEFAULT 0
                    )
                """)
                columns = {
                    row[1] for row in db.execute("PRAGMA table_info(validations)").fetchall()
                }
                if "enforced" not in columns:
                    db.execute(
                        "ALTER TABLE validations "
                        "ADD COLUMN enforced INTEGER NOT NULL DEFAULT 0"
                    )
        except sqlite3.OperationalError as exc:
            raise RuntimeError(
                f"RMV cannot open SQLite database at {self.path}. "
                "The /data volume must be writable by container UID 10001."
            ) from exc

    def _connect(self):
        db = sqlite3.connect(self.path, timeout=5)
        db.execute("PRAGMA busy_timeout=5000")
        db.execute("PRAGMA synchronous=NORMAL")
        return db

    def save(self, result: ValidationResult, *, enforced: bool = False):
        data = result.as_dict()
        data["enforced"] = int(enforced)
        with self._connect() as db:
            db.execute("""
                INSERT OR REPLACE INTO validations
                (torrent_hash,torrent_name,category,status,reason,video_files,blocked_files,
                 largest_video_bytes,checked_at,enforced)
                VALUES (:torrent_hash,:torrent_name,:category,:status,:reason,:video_files,
                        :blocked_files,:largest_video_bytes,:checked_at,:enforced)
            """, data)

    def has(self, torrent_hash: str) -> bool:
        with self._connect() as db:
            return db.execute(
                "SELECT 1 FROM validations WHERE torrent_hash=?", (torrent_hash,)
            ).fetchone() is not None

    def has_enforced(self, torrent_hash: str) -> bool:
        with self._connect() as db:
            row = db.execute(
                "SELECT enforced FROM validations WHERE torrent_hash=?", (torrent_hash,)
            ).fetchone()
        return bool(row and row[0])

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
            enforced = db.execute(
                "SELECT COUNT(*) FROM validations WHERE enforced=1"
            ).fetchone()[0]
        counts = {k: v for k, v in rows}
        return {
            "total": sum(counts.values()),
            "approved": counts.get("approved", 0),
            "blocked": counts.get("blocked", 0),
            "enforced": enforced,
        }
