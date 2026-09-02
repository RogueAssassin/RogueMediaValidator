from pathlib import PurePosixPath
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .config import Settings
from .models import ValidationResult


def extension(name: str) -> str:
    return PurePosixPath(name).suffix.lower().lstrip(".")


def validate_payload(
    *, torrent_hash: str, torrent_name: str, category: str, files: list[dict], settings: "Settings"
) -> ValidationResult:
    videos: list[dict] = []
    blocked: list[str] = []

    for item in files:
        name = str(item.get("name", ""))
        ext = extension(name)
        if ext in settings.blocked_exts:
            blocked.append(name)
        if ext in settings.video_exts:
            videos.append(item)

    if blocked:
        return ValidationResult.now(
            torrent_hash=torrent_hash,
            torrent_name=torrent_name,
            category=category,
            status="blocked",
            reason=f"Blocked file type detected: {blocked[0]}",
            video_files=len(videos),
            blocked_files=len(blocked),
            largest_video_bytes=max((int(v.get("size", 0)) for v in videos), default=0),
        )

    if not videos:
        return ValidationResult.now(
            torrent_hash=torrent_hash,
            torrent_name=torrent_name,
            category=category,
            status="blocked",
            reason="No approved video file found",
            video_files=0,
            blocked_files=0,
            largest_video_bytes=0,
        )

    largest = max(int(v.get("size", 0)) for v in videos)
    minimum = settings.min_video_size_mb * 1024 * 1024
    if largest < minimum:
        return ValidationResult.now(
            torrent_hash=torrent_hash,
            torrent_name=torrent_name,
            category=category,
            status="blocked",
            reason=f"Largest video is below minimum size ({settings.min_video_size_mb} MB)",
            video_files=len(videos),
            blocked_files=0,
            largest_video_bytes=largest,
        )

    unknown = []
    for item in files:
        name = str(item.get("name", ""))
        ext = extension(name)
        if ext and ext not in settings.video_exts and ext not in settings.support_exts:
            unknown.append(name)

    if unknown:
        return ValidationResult.now(
            torrent_hash=torrent_hash,
            torrent_name=torrent_name,
            category=category,
            status="blocked",
            reason=f"Unapproved file type detected: {unknown[0]}",
            video_files=len(videos),
            blocked_files=0,
            largest_video_bytes=largest,
        )

    return ValidationResult.now(
        torrent_hash=torrent_hash,
        torrent_name=torrent_name,
        category=category,
        status="approved",
        reason="Verified media payload",
        video_files=len(videos),
        blocked_files=0,
        largest_video_bytes=largest,
    )
