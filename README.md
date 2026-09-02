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

[![Testing](https://img.shields.io/badge/TESTING-0.1.0-8b5cf6?style=for-the-badge&labelColor=45464d)](https://github.com/RogueAssassin/roguemediavalidator/tree/testing)
[![GHCR](https://img.shields.io/badge/GHCR-PACKAGE-5c6ac4?style=for-the-badge&logo=github&logoColor=white&labelColor=45464d)](https://github.com/RogueAssassin/roguemediavalidator/pkgs/container/roguemediavalidator)
[![CI](https://img.shields.io/github/actions/workflow/status/RogueAssassin/roguemediavalidator/ci.yml?branch=testing&style=for-the-badge&label=CI&labelColor=45464d)](https://github.com/RogueAssassin/roguemediavalidator/actions/workflows/ci.yml?query=branch%3Atesting)
[![Build](https://img.shields.io/github/actions/workflow/status/RogueAssassin/roguemediavalidator/container.yml?branch=testing&style=for-the-badge&label=BUILD&labelColor=45464d)](https://github.com/RogueAssassin/roguemediavalidator/actions/workflows/container.yml?query=branch%3Atesting)
![Runtime](https://img.shields.io/badge/RUNTIME-PYTHON%203.12-ff4fc8?style=for-the-badge&labelColor=45464d)
![Engine](https://img.shields.io/badge/ENGINE-DOCKER%20%7C%20PODMAN-00cbe6?style=for-the-badge&labelColor=45464d)
![Platform](https://img.shields.io/badge/PLATFORM-AMD64%20%7C%20ARM64-42d6a4?style=for-the-badge&labelColor=45464d)

</div>

RogueMediaValidator (RMV) is a lightweight pre-download validation service for qBittorrent-driven Radarr and Sonarr stacks. It checks the actual torrent file list, requires a real approved video payload, blocks executable/script content, fails closed on unknown file types and records every decision in a local SQLite audit history.

## Why RMV

Release names can look legitimate while the torrent payload is not. RMV validates torrent metadata itself before an automated download is allowed to continue.

## What RMV does

- Scopes validation to configured qBittorrent categories such as `radarr` and `sonarr`.
- Requires at least one approved video file.
- Rejects executable, installer and script extensions.
- Rejects unknown extensions by default instead of silently trusting them.
- Enforces a minimum real-video size sanity check.
- Runs in safe audit-only dry-run mode by default.
- Resumes approved torrents automatically when enforcement is enabled.
- Removes rejected torrents and optionally deletes their data.
- Records validation results in SQLite.
- Exposes a lightweight dashboard and read-only health/statistics APIs.
- Runs rootless-friendly with dropped Linux capabilities and `no-new-privileges`.

## Port model

RMV reserves **7811 as its internal application port**. The host-side port is independently configurable, so it can be moved without changing the container or integrations:

```env
RMV_HTTP_PORT=7811
```

Default mapping:

```text
host 7811 -> container 7811
```

If 7811 is already used on a host, set (for example) `RMV_HTTP_PORT=17811`; RMV still listens internally on 7811.

## Container images

Testing:

```text
ghcr.io/rogueassassin/roguemediavalidator:testing
```

Production:

```text
ghcr.io/rogueassassin/roguemediavalidator:latest
```

The persistent branch model matches the other Rogue projects: `testing` is active development and `main` is the stable channel.

## Install with Podman

```bash
mkdir -p /opt/media-server/roguemediavalidator/data
cd /opt/media-server/roguemediavalidator

curl -fsSL https://raw.githubusercontent.com/RogueAssassin/roguemediavalidator/testing/compose.yaml -o compose.yaml
curl -fsSL https://raw.githubusercontent.com/RogueAssassin/roguemediavalidator/testing/.env.example -o .env

podman network inspect media-net >/dev/null 2>&1 || podman network create media-net
podman compose --env-file .env -f compose.yaml pull
podman compose --env-file .env -f compose.yaml up -d
```

Open `http://localhost:7811`.

## Safe first run

Leave:

```env
RMV_DRY_RUN=true
```

during initial live-stack testing. RMV will record decisions without resuming, deleting or removing anything unexpectedly. After the activity log has been verified, switch to `RMV_DRY_RUN=false`.

qBittorrent should receive automated Radarr/Sonarr torrents paused so RMV can inspect the torrent file metadata before payload download begins.

## Validation policy

Default approved video formats:

```text
mkv mp4 m4v avi ts m2ts webm mov
```

Default supporting formats:

```text
srt ass ssa sub idx nfo jpg jpeg png txt
```

Default blocked formats include:

```text
exe scr com bat cmd msi msix ps1 psm1 vbs vbe js jse wsf wsh lnk pif cpl jar apk dll
```

A torrent containing an approved video plus a blocked or unknown payload still fails.

## Branding

The approved RMV artwork follows the same runtime-icon structure as RogueDashboard:

```text
app/static/icons/
└── roguemediavalidator-approved-128.png
```

The same mark is used by the application header, browser icon and GitHub repository presentation.

## Repository layout

```text
app/                    application, UI and validator
tests/                  policy regression tests
docs/                   architecture/install/testing documentation
Dockerfile              hardened image build
compose.yaml            Docker/Podman deployment
compose.podman.yaml     compatibility deployment alias
.env.example            safe configuration template
VERSION                 canonical version
MILESTONES.md           development roadmap
SECURITY.md             security guidance
CHANGELOG.md            release history
```

## CI and testing

CI runs Ruff, unit tests, Python bytecode compilation, Compose validation and a container build. GHCR publishing builds Linux amd64/arm64 images with provenance and SBOM metadata.

The initial CI failure was caused by Ruff findings in the first foundation code: modern UTC usage in `app/models.py` plus an unused `json` import in `app/store.py`. The validator import layout was also normalised. These are corrected in the testing revision.

See [docs/TESTING.md](docs/TESTING.md) and [MILESTONES.md](MILESTONES.md).

## Rogue ecosystem

RMV is designed to integrate with [RogueDashboard](https://github.com/RogueAssassin/RogueDashboard) after standalone validation is proven on the live media stack. RogueDashboard integration will consume RMV's lightweight APIs rather than container-engine access.

## License

MIT
