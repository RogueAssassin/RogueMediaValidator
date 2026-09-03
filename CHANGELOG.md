# Changelog

## 0.2.0 - testing

Operational-safety hardening milestone.

### Added

- Validation-policy fingerprints derived from the active payload policy.
- Automatic revalidation when video/support/blocked extension policy or minimum video size changes.
- Structured enforcement audit fields: `action`, `action_status`, and `action_error`.
- Failed qBittorrent actions remain unenforced so failure is not mistaken for successful handling.
- Action-failure statistics.
- Automatic SQLite schema migration for 0.1.x databases.

### Changed

- Docker and Podman now share one `compose.yaml`.
- Removed the obsolete `compose.podman.yaml`.
- Documentation and testing guidance now use one deployment path for both engines.
- Testing image advances to `0.2.0-testing`.

### Safety

- Existing torrent hashes are no longer permanently trusted after validation policy changes.
- Category discovery remains informational and does not grant enforcement scope.


## 0.1.3 - testing

Category discovery and safety-hardening stage.

### Added

- qBittorrent category discovery through the native categories API.
- Configured and discovered category reporting in service diagnostics.
- `RMV_QB_CATEGORY_REFRESH_SECONDS` with a bounded minimum refresh interval.
- Regression tests for category discovery, case-insensitive matching, wildcard scope and empty-scope safety.
- qBittorrent connection retries, bounded connection timeout/limits and serialized login handling.
- SQLite WAL mode and busy-timeout handling for safer concurrent background/API access.
- Graceful background-task cancellation during application shutdown.

### Changed

- Example media categories now use `tv,movies`.
- Empty `RMV_QB_CATEGORIES` now fails closed and manages no torrents.
- Managing every category now requires the explicit wildcard `RMV_QB_CATEGORIES=*`.
- README expanded with architecture, security boundary, category discovery, API, troubleshooting, Podman/Docker, enforcement and live-testing guidance.
- Testing image advances to `0.1.3-testing`.

### Safety

Category discovery is informational only. Newly discovered qBittorrent categories are not automatically added to enforcement scope.

## 0.1.2 - testing

Live inspection stage.

### Added

- All-state inspection for configured categories.
- Separate action-state safety gate.
- Active downloads such as `downloading` and `stalledDL` are inspected.
- Completed/seeding/upload torrents remain inspection-only.
- Faster default 2-second polling.
- Diagnostics report in-scope and actionable torrent counts separately.

## 0.1.1 - testing

Live-server readiness stage.

### Added

- Safe qBittorrent managed-state gate.
- qBittorrent version and connection diagnostics.
- Validation-cycle counters.
- Audit/enforcement state.
- qBittorrent session-expiry recovery.

## 0.1.0 - stable

First stable RogueMediaValidator base release.
