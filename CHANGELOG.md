# Changelog

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

### Release channels

- `main` -> `:latest` and `:0.1.0`
- `testing` -> `:testing`
