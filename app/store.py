import json
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
                        enforced INTEGER NOT NULL DEFAULT 0,
                        policy_fingerprint TEXT NOT NULL DEFAULT '',
                        action TEXT NOT NULL DEFAULT 'none',
                        action_status TEXT NOT NULL DEFAULT 'audit',
                        action_error TEXT
                    )
                """)
                db.execute("""
                    CREATE TABLE IF NOT EXISTS runtime_settings (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL
                    )
                """)
                columns = {
                    row[1] for row in db.execute("PRAGMA table_info(validations)").fetchall()
                }
                migrations = {
                    "enforced": "INTEGER NOT NULL DEFAULT 0",
                    "policy_fingerprint": "TEXT NOT NULL DEFAULT ''",
                    "action": "TEXT NOT NULL DEFAULT 'none'",
                    "action_status": "TEXT NOT NULL DEFAULT 'audit'",
                    "action_error": "TEXT",
                }
                for name, definition in migrations.items():
                    if name not in columns:
                        db.execute(
                            f"ALTER TABLE validations ADD COLUMN {name} {definition}"
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

    def save(
        self,
        result: ValidationResult,
        *,
        policy_fingerprint: str,
        enforced: bool = False,
        action: str = "none",
        action_status: str = "audit",
        action_error: str | None = None,
    ):
        data = result.as_dict()
        data.update(
            {
                "enforced": int(enforced),
                "policy_fingerprint": policy_fingerprint,
                "action": action,
                "action_status": action_status,
                "action_error": action_error,
            }
        )
        with self._connect() as db:
            db.execute("""
                INSERT OR REPLACE INTO validations
                (torrent_hash,torrent_name,category,status,reason,video_files,blocked_files,
                 largest_video_bytes,checked_at,enforced,policy_fingerprint,action,
                 action_status,action_error)
                VALUES (:torrent_hash,:torrent_name,:category,:status,:reason,:video_files,
                        :blocked_files,:largest_video_bytes,:checked_at,:enforced,
                        :policy_fingerprint,:action,:action_status,:action_error)
            """, data)

    def set_runtime_setting(self, key: str, value: str):
        with self._connect() as db:
            db.execute(
                """
                INSERT INTO runtime_settings(key, value)
                VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value
                """,
                (key, value),
            )

    def get_runtime_setting(self, key: str) -> str | None:
        with self._connect() as db:
            row = db.execute(
                "SELECT value FROM runtime_settings WHERE key=?",
                (key,),
            ).fetchone()
        return str(row[0]) if row else None

    def set_bootstrap_categories(self, categories: list[str]):
        normalized = sorted({x.strip().lower() for x in categories if x.strip()})
        self.set_runtime_setting("bootstrap_categories", json.dumps(normalized))
        self.set_runtime_setting("category_bootstrap_complete", "1")

    def bootstrap_categories(self) -> frozenset[str]:
        raw = self.get_runtime_setting("bootstrap_categories")
        if not raw:
            return frozenset()
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            return frozenset()
        if not isinstance(payload, list):
            return frozenset()
        return frozenset(str(x).strip().lower() for x in payload if str(x).strip())

    def category_bootstrap_complete(self) -> bool:
        return self.get_runtime_setting("category_bootstrap_complete") == "1"

    def has_current(self, torrent_hash: str, policy_fingerprint: str) -> bool:
        with self._connect() as db:
            row = db.execute(
                "SELECT 1 FROM validations WHERE torrent_hash=? AND policy_fingerprint=?",
                (torrent_hash, policy_fingerprint),
            ).fetchone()
        return row is not None

    def has_enforced_current(self, torrent_hash: str, policy_fingerprint: str) -> bool:
        with self._connect() as db:
            row = db.execute(
                """
                SELECT enforced
                FROM validations
                WHERE torrent_hash=? AND policy_fingerprint=?
                """,
                (torrent_hash, policy_fingerprint),
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
            action_failures = db.execute(
                "SELECT COUNT(*) FROM validations WHERE action_status='failed'"
            ).fetchone()[0]
        counts = {k: v for k, v in rows}
        return {
            "total": sum(counts.values()),
            "approved": counts.get("approved", 0),
            "blocked": counts.get("blocked", 0),
            "enforced": enforced,
            "action_failures": action_failures,
        }
