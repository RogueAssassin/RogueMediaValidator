<div align="center">

<table>
  <tr>
    <td width="220" align="center">
      <img src="https://raw.githubusercontent.com/RogueAssassin/roguemediavalidator/main/app/static/icons/roguemediavalidator-approved-128.png" width="128" height="128" alt="RogueMediaValidator logo">
    </td>
    <td align="left">
      <h1>RogueMediaValidator</h1>
      <p><strong>Validate. Protect. Automate.</strong></p>
      <p>Pre-download payload validation • qBittorrent • Radarr • Sonarr • Docker • Podman</p>
    </td>
  </tr>
</table>

[![Stable](https://img.shields.io/badge/STABLE-0.1.2-42d6a4?style=for-the-badge&labelColor=45464d)](https://github.com/RogueAssassin/roguemediavalidator/tree/main)
[![GHCR](https://img.shields.io/badge/GHCR-LATEST-5c6ac4?style=for-the-badge&logo=github&logoColor=white&labelColor=45464d)](https://github.com/RogueAssassin/roguemediavalidator/pkgs/container/roguemediavalidator)
[![CI](https://img.shields.io/github/actions/workflow/status/RogueAssassin/roguemediavalidator/ci.yml?branch=main&style=for-the-badge&label=CI&labelColor=45464d)](https://github.com/RogueAssassin/roguemediavalidator/actions/workflows/ci.yml?query=branch%3Amain)
[![Build](https://img.shields.io/github/actions/workflow/status/RogueAssassin/roguemediavalidator/container.yml?branch=main&style=for-the-badge&label=BUILD&labelColor=45464d)](https://github.com/RogueAssassin/roguemediavalidator/actions/workflows/container.yml?query=branch%3Amain)
![Runtime](https://img.shields.io/badge/RUNTIME-PYTHON%203.12-ff4fc8?style=for-the-badge&labelColor=45464d)
![Engine](https://img.shields.io/badge/ENGINE-DOCKER%20%7C%20PODMAN-00cbe6?style=for-the-badge&labelColor=45464d)
![Platform](https://img.shields.io/badge/PLATFORM-AMD64%20%7C%20ARM64-42d6a4?style=for-the-badge&labelColor=45464d)

</div>

RogueMediaValidator (RMV) is a lightweight pre-download validation service for qBittorrent-driven Radarr and Sonarr stacks. It validates the actual torrent file list, requires an approved video payload, rejects executable/script content, fails closed on unknown file types and records every decision in SQLite.

## Stable release

**v0.1.2** is the first live-ready RMV release validated against a real Radarr → qBittorrent workflow.

Production images:

```text
ghcr.io/rogueassassin/roguemediavalidator:latest
ghcr.io/rogueassassin/roguemediavalidator:0.1.2
```

Development continues on:

```text
ghcr.io/rogueassassin/roguemediavalidator:testing
```

## Live validation model

RMV separates **inspection** from **action**:

- Every torrent in configured Radarr/Sonarr categories is inspected as soon as qBittorrent exposes its file metadata, regardless of current state.
- Active download states such as paused/stopped, queued, metadata, downloading and stalled states are actionable.
- Completed/seeding/upload states can be audited but are never deleted by RMV.
- Approved paused/stopped torrents can be resumed automatically when enforcement is enabled.
- Blocked torrents can be removed with their payload while still in the download lifecycle.
- Dry-run remains the safe default for a fresh install; a validated production server can explicitly set `RMV_DRY_RUN=false`.

The default poll interval is 2 seconds so validation happens quickly while remaining lightweight.

## Performance

Normal runtime logging is intentionally quiet:

- RMV keeps meaningful validation decisions, warnings and errors.
- qBittorrent HTTP request logging from `httpx/httpcore` is suppressed.
- Uvicorn access logging is disabled.
- `RMV_LOG_LEVEL` defaults to `INFO` and can be raised to `WARNING` for an even quieter production deployment.

This avoids unnecessary disk/console I/O while preserving useful operational records.

## Port model

RMV listens internally on TCP **7811**. The host port is independently configurable:

```env
RMV_HTTP_PORT=7811
```

## Podman install

```bash
mkdir -p /opt/media-server/roguemediavalidator
cd /opt/media-server/roguemediavalidator

curl -fsSL https://raw.githubusercontent.com/RogueAssassin/roguemediavalidator/main/compose.podman.yaml -o compose.podman.yaml
curl -fsSL https://raw.githubusercontent.com/RogueAssassin/roguemediavalidator/main/.env.example -o .env

podman network inspect media-net >/dev/null 2>&1 || podman network create media-net
podman compose --env-file .env -f compose.podman.yaml pull
podman compose --env-file .env -f compose.podman.yaml up -d
```

The Podman compose uses a managed named volume with `:U` ownership handling so SQLite is writable under rootless Podman.

## Production enforcement

Fresh installs intentionally start with:

```env
RMV_DRY_RUN=true
```

After validating the stack, change the live server to:

```env
RMV_DRY_RUN=false
RMV_LOG_LEVEL=INFO
```

and recreate the container.

## Validation policy

Approved video types:

```text
mkv mp4 m4v avi ts m2ts webm mov
```

Supporting types:

```text
srt ass ssa sub idx nfo jpg jpeg png txt
```

Blocked types include:

```text
exe scr com bat cmd msi msix ps1 psm1 vbs vbe js jse wsf wsh lnk pif cpl jar apk dll
```

Any unknown extension fails closed.

## CI

CI runs Ruff, unit tests, Python bytecode compilation, Compose validation and a container build. GHCR publishing builds Linux amd64/arm64 images with provenance and SBOM metadata.

## Rogue ecosystem

RogueDashboard integration is planned after standalone production enforcement is proven.

## License

MIT
