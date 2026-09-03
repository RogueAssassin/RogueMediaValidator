# RogueMediaValidator milestones

## 0.1.x — Core validation and safe discovery

- qBittorrent authentication and torrent metadata inspection
- explicit qBittorrent category scoping
- qBittorrent category discovery without automatic permission expansion
- fail-closed behavior when no categories are configured
- strict video/support allowlists
- executable/script rejection
- minimum video-size sanity check
- dry-run and enforcement modes
- SQLite audit history with WAL/busy-timeout hardening
- responsive Rogue-style UI
- Docker/Podman and GHCR CI
- approved RMV branding
- fixed internal application port 7811 with configurable host mapping
- graceful shutdown and bounded qBittorrent connection behavior

## 0.2.x — Operational safety

- structured reason codes and complete per-file decision detail
- policy fingerprint/version so policy changes trigger revalidation
- richer action outcome and idempotency records
- configurable quarantine behavior
- API authentication before administrative/write APIs are introduced
- policy editor with validation and test mode
- richer runtime connection diagnostics
- audit retention, export and backup controls
- optional post-download media signature/ffprobe validation

## 0.3.x — Arr integration

- optional Radarr/Sonarr failed-download feedback
- automatic retry/blacklist workflow
- source/indexer context where available
- notification/webhook events
- optional Arr-assisted category mapping while preserving qBittorrent as the enforcement source of truth

## 0.4.x — Rogue ecosystem

- native RogueDashboard health/status card
- configured/discovered category visibility
- recent validation and blocked-reason widgets
- shared branding conventions and deployment helpers
- stack-health integration without Docker/Podman socket access
