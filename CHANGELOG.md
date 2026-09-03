# Changelog

## 0.4.0 - testing

Multi-client architecture and guided installation milestone.

### Added

- Torrent-client adapter interface separating the validator from provider-specific APIs.
- qBittorrent adapter moved behind the shared provider interface.
- Transmission adapter with modern JSON-RPC support, legacy Transmission 4.0 RPC fallback, CSRF session handling and optional Basic authentication.
- Transmission label discovery and multi-label scope matching.
- Provider-normalized torrent state, file metadata, resume and delete behavior.
- Guided `/setup` Installation page.
- Supported/planned torrent-client selector.
- Connection testing before setup can be saved.
- Provider-specific managed-scope persistence.
- Setup configuration persistence inside RMV's private data volume.
- Automatic redirect to Installation on a fresh unconfigured deployment.
- Generic `torrent_client` diagnostics/API model.
- Setup write lock controlled by `RMV_SETUP_UNLOCK`.
- Setup and Transmission regression tests.

### Changed

- Dashboard terminology is now provider-neutral.
- qBittorrent categories and Transmission labels are normalized as RMV scopes.
- Fresh `.env.example` no longer assumes qBittorrent.
- The external container network is configurable through `RMV_NETWORK` while `media-net` remains the default.
- New generic `RMV_TORRENT_*` settings replace qBittorrent-specific settings for fresh installs.
- Legacy `RMV_QB_*` settings remain supported for 0.3.x upgrades.
- Testing image advances to `0.4.0-testing`.

### Security

- RMV still does not require Docker or Podman socket access.
- Provider setup communicates only with the selected torrent client API.
- Setup writes lock after configuration unless explicitly unlocked.
- Client passwords are not returned through diagnostics.


## 0.3.1 - testing

Dashboard simplification and visual cleanup.

### Changed

- Removed the unused Dashboard, Activity and Policy navigation tabs.
- Replaced the permanent sidebar with a compact top application bar.
- Kept Diagnostics as a single clear utility action.
- Expanded the main canvas to use the full available width.
- Simplified the dashboard around validation totals, qBittorrent health, managed categories and recent validation history.
- Added explicit action-failure visibility to the primary metrics.
- Condensed category source, runtime state and policy details into clearer status cards.
- Moved verbose policy/runtime information into an expandable Technical details section.
- Improved responsive behavior for desktop, tablet and mobile layouts.
- Testing image advances to `0.3.1-testing`.

### UI

The dashboard is intentionally read-focused. RMV's current administrative APIs remain read-only, so the interface does not present fake or non-functional configuration navigation.


## 0.3.0 - testing

First-run category automation stage.

### Added

- One-time automatic qBittorrent category bootstrap when `RMV_QB_CATEGORIES` is blank.
- `RMV_QB_AUTO_BOOTSTRAP_CATEGORIES` setting, enabled by default.
- Persistent managed category bootstrap state in SQLite `runtime_settings`.
- Runtime diagnostics for environment, managed and discovered category sets.
- Category source reporting: `environment`, `auto_bootstrap`, or `none`.
- Regression tests covering first bootstrap, persistence, explicit overrides, disabled bootstrap and no silent enrolment of later categories.

### Changed

- The default `.env.example` now leaves `RMV_QB_CATEGORIES` blank so first-run discovery can configure scope automatically.
- Explicit environment categories always override the persisted bootstrap set.
- New qBittorrent categories discovered after initial bootstrap remain informational and are not silently added.
- Testing image advances to `0.3.0-testing`.

### Safety

- Auto-bootstrap is one-time rather than continuous, preventing category permission creep.
- Dry-run remains enabled by default, so first-run bootstrap does not itself cause resume/delete actions.


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
