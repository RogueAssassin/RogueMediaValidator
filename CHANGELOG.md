# Changelog

## 1.3.0 - 2026-10-23

- Moved the container image to Python 3.14 (`python:3.14-slim`).
- Aligned the release with RogueDashboard 2.3.0 and RogueForge 2.3.0.

## 1.1.1 - 2026-10-11

- Changed the Compose pull policy default to `missing` (`RMV_PULL_POLICY`) so the container can be recreated while the registry is unreachable; `update.sh` always pulls explicitly.
- Added the optional `RMV_HTTP_BIND`, `RMV_MEM_LIMIT`, `RMV_PIDS_LIMIT` and `RMV_RUNTIME` settings and bounded container log rotation; existing `.env` files keep working without them.
- Made `update.sh` pull before changing deployment files, take a lock and roll back the deployment files and image when verification or the health check fails.
- Moved update backups from `/tmp` to `backups/update` (last ten kept) and added `compose.override.yaml` support.
- Published images from the `VERSION` file after lint and tests pass, and smoke tested the image under the read-only, non-root, capability-free runtime.
- Added Dependabot and pinned LF line endings for container files.

## 1.1.0 - 2026-09-07

- Promoted the validated RogueMediaValidator v1.1.0 testing baseline to production.
- Standardised the README, changelog, environment-file presentation and update workflow with RogueDashboard and RogueForge.
- Added the Rogue ecosystem overview and canonical `/opt/media-server/roguemediavalidator` deployment guidance.
- Added the Rogue-style `update.sh` workflow for production, testing and pinned-version updates.
- Hardened Compose with a read-only root filesystem, bounded `/tmp`, explicit health checking, stop grace period, pull policy and Rogue ecosystem labels.
- Kept the existing named SQLite volume contract unchanged so testing does not strand v1.0.0 state.
- Added OCI image metadata and a clean SIGTERM shutdown contract to the container image.
- Added updater syntax validation to the automated test workflow.
- Kept all v1.0.0 provider, policy, automation, notification, audit and safety behavior intact.

## 1.0.0

- First stable provider-neutral RogueMediaValidator release.
- Added qBittorrent, Transmission, Deluge, rTorrent/ruTorrent and aria2 support.
- Added browser setup, dry-run enforcement controls, fail-closed managed scopes and policy fingerprinting.
- Added quarantine/hold workflows and capability-aware payload deletion.
- Added Radarr, Sonarr and generic webhook automation feedback.
- Added operational notifications, audit export/retention and RogueDashboard status integration.
- Added Docker and Podman deployment with amd64/arm64 GHCR publishing, SBOM and provenance.

## 0.9.0

- Added operational monitoring, notifications, audit export/retention and status integration.

## 0.8.0

- Added provider-neutral TV/movie automation feedback with Radarr, Sonarr and generic webhook integrations.

## 0.7.0

- Added provider-neutral quarantine/hold support and quarantine auditing.

## 0.6.0

- Added authenticated administration, UI-managed scopes and explicit configuration ownership.

## 0.5.0

- Completed the supported headless torrent-provider set with Deluge, rTorrent/ruTorrent and aria2.
