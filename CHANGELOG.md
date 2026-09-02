# Changelog

## 0.1.2 - stable

First live-ready RogueMediaValidator release.

### Added

- All-state torrent inspection for configured Radarr/Sonarr categories.
- Separate action-state safety gate for active download lifecycle states.
- Active-download inspection for queued, metadata, downloading and stalled states.
- Completed/seeding/upload inspection without destructive action.
- qBittorrent connection/version diagnostics and session re-authentication.
- Dry-run-to-enforcement reprocessing support.
- Audit/handled state in validation history.
- 2-second default polling for early file-list validation.
- Configurable `RMV_LOG_LEVEL`.

### Performance

- Suppressed routine `httpx/httpcore` request logs.
- Disabled Uvicorn access logging.
- Kept one meaningful RMV decision log per validated torrent plus warnings/errors.
- Avoided repeated payload validation after a torrent has already been handled.

### Fixed

- Rootless Podman SQLite permissions with managed volume ownership handling.
- qBittorrent successful 204/empty-body authentication responses.
- qBittorrent expired-session retry.
- CI/Ruff issues from earlier testing stages.

### Release channels

- `main` -> `:latest` and `:0.1.2`
- `testing` -> `:testing`

## 0.1.1 - testing

Live-server readiness stage.

## 0.1.0 - stable

Initial stable foundation.
