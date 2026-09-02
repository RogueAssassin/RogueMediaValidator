from dataclasses import asdict, dataclass
from datetime import UTC, datetime


@dataclass(slots=True)
class ValidationResult:
    torrent_hash: str
    torrent_name: str
    category: str
    status: str
    reason: str
    video_files: int
    blocked_files: int
    largest_video_bytes: int
    checked_at: str

    @classmethod
    def now(cls, **kwargs):
        return cls(checked_at=datetime.now(UTC).isoformat(), **kwargs)

    def as_dict(self):
        return asdict(self)
