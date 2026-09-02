# RogueMediaValidator

**Validate. Protect. Automate.**

RogueMediaValidator (RMV) is a lightweight pre-download validation service for qBittorrent-driven Radarr and Sonarr stacks. It inspects the actual torrent file list, requires approved video payloads, rejects executable/script content, fails closed on unknown file types, records every decision, and exposes a simple web dashboard/API.

## Why RMV

Release names can look legitimate while the torrent payload is not. RMV validates the payload metadata itself before allowing an automated download to continue.

## Testing release: 0.1.0

The initial testing build includes:

- qBittorrent Web API integration
- category scoping for `radarr` and `sonarr`
- strict video/supporting-file allowlists
- executable/script blocklist
- minimum video size validation
- dry-run mode enabled by default
- automatic resume of approved torrents
- automatic removal/deletion of rejected torrents when enforcement is enabled
- SQLite audit history
- responsive Rogue-style dashboard
- `/api/health`, `/api/stats`, and `/api/validations`
- Docker and Podman-compatible compose
- non-root container, dropped capabilities and no-new-privileges
- GitHub CI and GHCR multi-architecture publishing

## Safe first run

Copy `.env.example` to `.env`, set the qBittorrent URL/credentials and leave `RMV_DRY_RUN=true` for initial testing. Add automated Radarr/Sonarr torrents paused so RMV can inspect metadata without downloading their payload.

```bash
cp .env.example .env
podman compose up -d
```

Dashboard: `http://localhost:7810`

Once decisions look correct, change `RMV_DRY_RUN=false` and restart RMV.

## Validation policy

At least one approved video file is required. Every non-video file must be on the supporting-file allowlist. Known executable/script extensions are rejected immediately. This strict fail-closed policy is deliberate.

Default video formats: `mkv mp4 m4v avi ts m2ts webm mov`

Default support formats: `srt ass ssa sub idx nfo jpg jpeg png txt`

Default blocked formats include: `exe scr com bat cmd msi msix ps1 psm1 vbs vbe js jse wsf wsh lnk pif cpl jar apk dll`

## Branch model

- `main` → stable / `latest`
- `testing` → active testing / `testing`

## Roadmap

0.1.x focuses on qBittorrent payload validation and safe enforcement. Next stages will add Radarr/Sonarr failed-download feedback, authenticated settings editing, richer policy controls, event/webhook integration and RogueDashboard native integration.
