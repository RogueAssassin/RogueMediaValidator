# Changelog

## 0.1.1 - testing

Live-server readiness stage.

### Added

- Safe qBittorrent managed-state gate. RMV now defaults to validating only `pausedDL` and `stoppedDL` torrents in configured Radarr/Sonarr categories.
- qBittorrent version and connection diagnostics through `/api/health` and `/api/diagnostics`.
- Validation-cycle counters for seen, eligible and processed torrents.
- Audit/enforcement state in validation history.
- Session-expiry recovery: qBittorrent 401/403 responses trigger one automatic re-authentication and retry.
- Regression coverage for managed torrent states, re-authentication and dry-run-to-enforcement transitions.

### Changed

- Dry-run results remain visible in history but do not permanently prevent the same paused torrent from being reprocessed after enforcement is enabled.
- Testing image advances to `0.1.1-testing`.
- Dashboard now shows qBittorrent connectivity/version and whether a decision was Audit or Enforced.

## 0.1.0 - stable

First stable RogueMediaValidator base release.

### Added

- qBittorrent metadata polling and category scoping.
- Strict approved-video and supporting-file allowlists.
- Executable/script blocklist and fail-closed unknown-extension handling.
- Minimum video-size validation.
- Dry-run safety mode and enforcement controls.
- SQLite audit history and responsive dashboard.
- Docker/Podman deployment and GHCR multi-architecture publishing.
- Approved RMV icon integrated into the UI and GitHub presentation.
- Internal application port 7811 with independently configurable host mapping.
- Regression tests for SQLite persistence and qBittorrent authentication.

### Fixed

- Rootless Podman SQLite startup failure by moving persistent data to a managed volume with Podman ownership handling.
- qBittorrent authentication compatibility for successful empty-body 2xx/204 login responses.
- CI Ruff findings for modern `datetime.UTC` usage and unused imports.
- Container health check and Compose mapping use the dedicated RMV internal port.
