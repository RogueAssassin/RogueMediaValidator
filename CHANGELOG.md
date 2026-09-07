# Changelog

## 1.2.0 (testing)

- Advanced the permanent testing branch after successful v1.1.0 production promotion.
- Preserved the v1.1.0 provider, policy, automation, notification, audit, updater and container-hardening baseline.
- Added no new environment revision because this is a clean development baseline only.

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
