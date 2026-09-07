<div align="center">

<img src="https://raw.githubusercontent.com/RogueAssassin/RogueMediaValidator/testing/app/static/icons/roguemediavalidator-approved-128.png" width="128" height="128" alt="RogueMediaValidator logo">

# RogueMediaValidator

**Validate. Protect. Automate.**

Provider-neutral torrent payload validation and enforcement for Docker and Podman media stacks.

[![Release](https://img.shields.io/badge/RELEASE-1.1.0%20TESTING-8b5cf6?style=for-the-badge&labelColor=45464d)](https://github.com/RogueAssassin/RogueMediaValidator/tree/testing)
[![CI](https://img.shields.io/github/actions/workflow/status/RogueAssassin/RogueMediaValidator/ci.yml?branch=testing&style=for-the-badge&label=CI&labelColor=45464d)](https://github.com/RogueAssassin/RogueMediaValidator/actions/workflows/ci.yml?query=branch%3Atesting)
[![Build](https://img.shields.io/github/actions/workflow/status/RogueAssassin/RogueMediaValidator/container.yml?branch=testing&style=for-the-badge&label=BUILD&labelColor=45464d)](https://github.com/RogueAssassin/RogueMediaValidator/actions/workflows/container.yml?query=branch%3Atesting)
![Engine](https://img.shields.io/badge/ENGINE-DOCKER%20%7C%20PODMAN-00cbe6?style=for-the-badge&labelColor=45464d)
![Platform](https://img.shields.io/badge/PLATFORM-AMD64%20%7C%20ARM64-42d6a4?style=for-the-badge&labelColor=45464d)

</div>

RogueMediaValidator (RMV) is the validation and protection layer for automated torrent workflows. It inspects declared payloads before automation continues, records every decision in SQLite and can resume approved downloads, quarantine rejected downloads or remove rejected torrents when enforcement is enabled.

RMV stays provider-neutral: torrent clients, media automation and notifications are isolated behind adapters so the validation policy is not tied to one application.

## Highlights

- qBittorrent, Transmission, Deluge, rTorrent/ruTorrent and aria2 support
- guided browser setup with connection, capability and scope discovery
- dry-run by default with explicit enforcement controls
- fail-closed managed-scope behavior
- quarantine/hold support for rejected downloads
- Radarr, Sonarr and generic automation feedback
- operational webhook notifications
- persistent audit history with CSV/JSON export and retention
- health, readiness and compact RogueDashboard status endpoints
- Docker and rootless Podman support from one `compose.yaml`
- no Docker or Podman socket mount required
- hardened unprivileged container with a read-only root filesystem

## Rogue ecosystem

| Service | What it does |
| --- | --- |
| [**RogueDashboard**](https://github.com/RogueAssassin/RogueDashboard) | Lightweight media-server visibility, health, uptime, incidents, alerts and service overview. |
| [**RogueForge**](https://github.com/RogueAssassin/RogueForge) | Docker/Podman stack management, verified updates, live logs, terminals and operational troubleshooting. |
| **RogueMediaValidator** | Torrent/media validation and protection for download workflows, including policy enforcement and diagnostics. |
| [**RogueRoute-GPX**](https://github.com/RogueAssassin/RogueRoute-GPX) | Routing and GPX services for route generation, processing and related mapping workflows. |

## Default layout

```text
/opt/media-server/
├── roguemediavalidator/
│   ├── compose.yaml
│   ├── .env
│   └── update.sh
├── rogueforge/
├── roguedashboard/
├── qbittorrent/
├── radarr/
├── sonarr/
└── ...
```

RMV keeps its SQLite state in the persistent `roguemediavalidator-data` container volume. Normal updates never remove that volume.

## Quick install

```bash
mkdir -p /opt/media-server/roguemediavalidator
cd /opt/media-server/roguemediavalidator

curl -fsSL https://raw.githubusercontent.com/RogueAssassin/RogueMediaValidator/testing/compose.yaml -o compose.yaml
curl -fsSL https://raw.githubusercontent.com/RogueAssassin/RogueMediaValidator/testing/.env.example -o .env
curl -fsSL https://raw.githubusercontent.com/RogueAssassin/RogueMediaValidator/testing/update.sh -o update.sh
chmod 600 .env
chmod +x update.sh
nano .env
```

Keep `RMV_DRY_RUN=true` for first setup. Set a strong `RMV_ADMIN_USERNAME` and `RMV_ADMIN_PASSWORD`, and make sure `RMV_NETWORK` matches the network used by your torrent client.

Podman:

```bash
podman network inspect media-net >/dev/null 2>&1 || podman network create media-net
podman compose --env-file .env -f compose.yaml pull
podman compose --env-file .env -f compose.yaml up -d
```

Docker:

```bash
docker network inspect media-net >/dev/null 2>&1 || docker network create media-net
docker compose --env-file .env -f compose.yaml pull
docker compose --env-file .env -f compose.yaml up -d
```

Open:

```text
http://HOST:7811
```

Leave the torrent-client environment values blank to use the browser setup wizard. Test the connection, verify the discovered managed scopes and only change `RMV_DRY_RUN=false` after Diagnostics shows the expected behavior.

## Supported torrent clients

| Client | Scope source | Resume | Pause/hold | Remove torrent | Remove payload data |
| --- | --- | ---: | ---: | ---: | ---: |
| qBittorrent | Categories | Yes | Yes | Yes | Yes |
| Transmission | Labels | Yes | Yes | Yes | Yes |
| Deluge | Label or download path | Yes | Yes | Yes | Yes |
| rTorrent / ruTorrent | custom1 or download path | Yes | Yes | Yes | No |
| aria2 | Download path | Yes | Yes | Yes | No |

When a provider cannot guarantee local payload deletion, RMV records a limited action instead of reporting full deletion success.

## Updating

Testing:

```bash
cd /opt/media-server/roguemediavalidator
./update.sh testing
```

Pinned testing build:

```bash
./update.sh 1.1.0-testing
```

Stable production after promotion:

```bash
./update.sh latest
```

The updater follows the RogueDashboard/RogueForge pattern: it detects Docker or Podman, preserves the existing `.env` and persistent volume, backs up deployment files, pulls the requested image, recreates RMV, verifies the running image and checks `/healthz` before refreshing the updater itself.

## Monitoring

```text
GET /healthz
GET /readyz
GET /api/status
```

- `/healthz` is process liveness.
- `/readyz` returns HTTP 200 only when RMV is configured, connected and managing at least one scope.
- `/api/status` is the compact no-secret integration payload for RogueDashboard and other monitoring.

## Persistent data

Keep the named `roguemediavalidator-data` volume between upgrades. Do not use `compose down -v` unless deleting RMV setup state, audit history and the SQLite database is intentional.

## Security model

RogueMediaValidator:

- runs as an unprivileged user
- uses a read-only root filesystem with a bounded writable `/tmp`
- drops all Linux capabilities and enables `no-new-privileges`
- never requires the Docker or Podman socket
- keeps provider credentials and integration secrets server-side
- starts in dry-run mode and fails closed for unknown payload extensions

Keep RMV on a trusted network and use HTTPS/authentication before exposing it beyond that network.

## Documentation

- [Installation](docs/INSTALL.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Security](SECURITY.md)
- [Changelog](CHANGELOG.md)

## Release channels

Testing:

```text
ghcr.io/rogueassassin/roguemediavalidator:testing
ghcr.io/rogueassassin/roguemediavalidator:1.1.0-testing
```

Stable production remains:

```text
ghcr.io/rogueassassin/roguemediavalidator:latest
ghcr.io/rogueassassin/roguemediavalidator:1.0.0
```

The permanent `testing` branch is the proving ground for the next release. `main` remains the stable production branch until testing is validated.
