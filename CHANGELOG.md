# Changelog

## 0.7.0 - testing - 2026-09-05

Quarantine and deep-media-validation milestone.

### Added in the first 0.7.0 testing build

- Provider-neutral `pause()`/hold capability across qBittorrent, Transmission, Deluge, rTorrent/ruTorrent and aria2.
- Opt-in `RMV_QUARANTINE_REJECTED` setting, disabled by default.
- Rejected actionable torrents can now be paused/stopped and held instead of deleted.
- Persistent SQLite quarantine records with torrent, provider, scope, reason and lifecycle timestamps.
- `GET /api/quarantine` for held-item inspection.
- Dashboard quarantine metric and Settings visibility.
- Quarantine action auditing using `action=quarantine` and `action_status=held`.
- Regression tests proving quarantine takes precedence over deletion only when explicitly enabled.
- Existing delete/remove behavior remains unchanged when quarantine is disabled.

### Remaining in the 0.7.x testing cycle

- Structured per-file validation reason detail.
- Quarantine operator review/recheck/release workflow.
- Optional post-download ffprobe validation.
- Media/container signature checks where practical.
- Bounded media-path access and disk/path safety controls.
- Quarantine retention and cleanup policy.
- Improved history filtering and detailed validation inspection.

### Safety

- Quarantine is opt-in and does not change existing 0.6.x behavior by default.
- A quarantined torrent must be paused/stopped through the provider API; RMV does not label an actively downloading torrent as safely held.
- Quarantine preserves payload data for review and avoids destructive deletion when enabled.


## 0.6.0 - testing - 2026-09-05

Administration and operator-control development milestone.

### Added in the first 0.6.0 testing build

- Authenticated administrative Settings page protected by explicit `RMV_ADMIN_USERNAME` and `RMV_ADMIN_PASSWORD` credentials.
- Protected `/api/admin/settings` and `/api/admin/scopes` endpoints.
- UI-managed provider scopes with explicit add/remove control.
- Provider-specific persistence for manually managed scopes, including an intentional empty/fail-closed selection.
- Clear environment-versus-UI-versus-bootstrap scope ownership.
- Environment scope priority: `RMV_TORRENT_SCOPES` cannot be overridden from the UI.
- Dashboard navigation to the new Settings area.
- Regression coverage for manual-scope persistence, isolation, precedence and fail-closed behavior.

### Remaining in this testing cycle
- Structured per-file validation reasons in the UI and API.
- Improved validation-history filtering and detail.
- Safer confirmation flows for destructive settings.
- Clearer dry-run/enforcement state and activation guidance.
- Configuration validation with actionable operator errors.
- Upgrade-safe persistence and schema migration coverage.
- Continued regression coverage for every supported torrent provider.

### Road to 1.0

- 0.7.0: quarantine and optional deep/post-download media validation.
- 0.8.0: provider-neutral TV/movie automation integrations, with Radarr and Sonarr as first-class providers rather than hard-coded core dependencies.
- 0.9.0: notifications, RogueDashboard/health integration, audit lifecycle and operational polish.
- 0.9.x: release-candidate hardening, migration/security testing and feature freeze.
- 1.0.0: stable production contract.

### Safety

- 0.6.0 testing continues to default to dry-run.
- Scope management must fail closed and must not silently broaden enforcement.
- Existing torrent-provider behavior remains provider-neutral.


## 0.5.0 - 2026-09-03

Complete headless torrent-provider support and compatibility cleanup.

### Added

- Deluge Web JSON-RPC adapter.
- Deluge daemon auto-connect handling.
- Deluge label scope with download-location fallback.
- rTorrent/ruTorrent XML-RPC adapter.
- rTorrent custom1 scope with directory fallback.
- aria2 JSON-RPC BitTorrent adapter.
- aria2 RPC secret support.
- Provider `supports_delete_data` capability.
- Limited enforcement state for providers that cannot guarantee local payload deletion.
- Dashboard Action issues metric for failed + limited actions.
- Provider-specific credential labels and cleanup capability in Installation.
- Direct regression tests for qBittorrent, Transmission, Deluge, rTorrent and aria2.

### Changed

- Stable release version is `0.5.0`; testing images remain available from the permanent testing branch.
- Core configuration is now exclusively `RMV_TORRENT_*`.
- Scope persistence API is fully provider-neutral.
- Diagnostics are fully provider-neutral.
- Package description no longer identifies RMV as qBittorrent-based.

### Removed

- Obsolete `app/qbittorrent.py` compatibility wrapper.
- Active `RMV_QB_*` compatibility configuration.
- qBittorrent compatibility aliases from health/service diagnostics.
- Legacy category-named storage helper APIs.
- Planned status for Deluge and rTorrent.

### Safety

- RMV never claims payload deletion succeeded when a provider cannot guarantee it.
- rTorrent and aria2 record `action_status=limited` when delete-data was requested.
- Docker/Podman sockets remain unnecessary.


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
