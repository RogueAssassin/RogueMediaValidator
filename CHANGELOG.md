# Changelog

## 0.1.0 - testing

Initial RogueMediaValidator testing foundation.

### Added

- qBittorrent metadata polling and category scoping.
- Strict approved-video and supporting-file allowlists.
- Executable/script blocklist and fail-closed unknown-extension handling.
- Minimum video-size validation.
- Dry-run safety mode and enforcement controls.
- SQLite audit history and responsive dashboard.
- Docker/Podman deployment and GHCR multi-architecture publishing.
- Approved RMV icon integrated into the UI and GitHub presentation.
- Permanent `testing` branch model matching the Rogue project family.
- Internal application port 7811 with independently configurable `RMV_HTTP_PORT`.

### Fixed

- CI Ruff failure caused by the `ValidationResult` import appearing after the `TYPE_CHECKING` block.
- Container health check and Compose mapping now use the dedicated RMV internal port.
