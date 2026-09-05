# Changelog

## 1.0.0 - 2026-09-05

First production release.

### Core

- Provider-neutral torrent validation for qBittorrent, Transmission, Deluge, rTorrent/ruTorrent and aria2.
- Guided browser setup with connection, version, capability and scope discovery.
- Dry-run by default with explicit enforcement controls.
- Fail-closed managed-scope behavior with environment, UI and one-time bootstrap ownership.
- Policy fingerprinting and automatic revalidation after policy changes.
- SQLite persistence for configuration, validation and operational state.

### Enforcement

- Resume approved actionable downloads.
- Remove rejected torrents when configured.
- Optional quarantine/hold workflow for rejected actionable downloads.
- Provider capability reporting for payload deletion.
- Limited-action auditing when a provider cannot guarantee local payload deletion.
- Completed/seeding torrents remain inspection-only.

### Administration

- Authenticated Settings area.
- UI-managed scopes.
- Quarantine visibility.
- Automation and notification connection testing.
- Audit export and retention controls.
- Diagnostics without exposing provider passwords, API keys or admin credentials.

### Media automation

- Provider-neutral automation layer.
- Radarr and Sonarr first-class adapters.
- Generic webhook automation integration.
- Multiple automation instances.
- Queue correlation by torrent hash/downloadId.
- Upstream rejection/blocklist feedback without double-removing the torrent from the download client.
- Feedback failure isolation and duplicate-success suppression.

### Operations

- Best-effort webhook notifications for approved, rejected, failed, limited and quarantined outcomes.
- Notification delivery auditing.
- `/healthz` liveness endpoint.
- `/readyz` operational readiness endpoint.
- Compact `/api/status` integration endpoint.
- Authenticated CSV/JSON audit export.
- Configurable age- and count-based audit retention.
- Docker and Podman support from one Compose file.
- Multi-architecture container publishing for amd64 and arm64.
- SBOM and provenance enabled for published images.

### Release cleanup

- Removed development milestone and roadmap documentation.
- Removed the obsolete standalone testing-plan document.
- Removed unused concept artwork.
- Replaced development-heavy README/install text with production-facing documentation.
- Removed milestone/version labels from runtime configuration and Settings UI.
- Corrected GHCR version tags to publish `1.0.0-testing` from testing and `1.0.0` from main.

## 0.9.0 - 2026-09-05

Operational monitoring, notifications, audit export/retention and status integration.

## 0.8.0 - 2026-09-05

Provider-neutral TV/movie automation feedback with Radarr, Sonarr and generic webhook integrations.

## 0.7.0 - 2026-09-05

Provider-neutral quarantine/hold support and quarantine auditing.

## 0.6.0 - 2026-09-05

Authenticated administration, UI-managed scopes and explicit configuration ownership.

## 0.5.0 - 2026-09-03

Completed the supported headless torrent-provider set with Deluge, rTorrent/ruTorrent and aria2.
