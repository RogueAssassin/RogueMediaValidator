# RogueMediaValidator milestones

## 0.1.x — Core validation

- qBittorrent authentication and torrent metadata inspection
- Radarr/Sonarr category scoping
- strict video/support allowlists
- executable/script rejection
- minimum video-size sanity check
- dry-run and enforcement modes
- SQLite audit history
- responsive Rogue-style UI
- Docker/Podman and GHCR CI
- approved RMV branding
- fixed internal application port 7811 with configurable host mapping

## 0.2.x — Operational safety

- richer reason codes and per-file decision detail
- safer retry/idempotency handling
- configurable quarantine behavior
- API authentication for administrative operations
- policy editor with validation and test mode
- runtime connection diagnostics

## 0.3.x — Arr integration

- Radarr/Sonarr failed-download feedback
- automatic retry/blacklist workflow
- source/indexer context where available
- notification/webhook events

## 0.4.x — Rogue ecosystem

- native RogueDashboard health/status card
- recent validation and blocked-reason widgets
- shared branding conventions and deployment helpers
- stack-health integration without Docker/Podman socket access
