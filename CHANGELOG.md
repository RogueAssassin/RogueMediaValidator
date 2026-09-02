# Changelog

## 0.1.2 - testing

Live inspection stage.

### Added

- All-state inspection for configured Radarr/Sonarr categories. RMV now checks torrent file metadata regardless of qBittorrent state.
- Separate action-state safety gate. Resume/delete actions are limited to download-lifecycle states.
- Active downloads such as `downloading` and `stalledDL` are now inspected, allowing RMV to catch releases that started before the first poll.
- Completed/seeding/upload torrents remain inspection-only and are never deleted by RMV.
- Faster default 2-second polling to reduce the delay between qBittorrent receiving metadata and RMV validating it.
- Diagnostics now report in-scope and actionable torrent counts separately.
- Tests for paused, active, stalled, completed/seeding and out-of-scope torrent handling.

### Changed

- Reduced normal runtime log I/O by suppressing qBittorrent HTTP client request logs and Uvicorn access logs; RMV validation decisions and warnings/errors remain visible.
- Added configurable `RMV_LOG_LEVEL` (default `INFO`).
- `RMV_QB_MANAGED_STATES` is replaced by `RMV_QB_INSPECT_ALL_STATES` and `RMV_QB_ACTION_STATES`.
- Validation history labels enforcement-complete rows as Handled rather than implying every row caused an action.
- Testing image advances to `0.1.2-testing`.

## 0.1.1 - testing

Live-server readiness stage.

### Added

- Safe qBittorrent managed-state gate.
- qBittorrent version and connection diagnostics.
- Validation-cycle counters.
- Audit/enforcement state in validation history.
- qBittorrent session-expiry recovery.
- Regression coverage for state gating and dry-run-to-enforcement transitions.

## 0.1.0 - stable

First stable RogueMediaValidator base release.
