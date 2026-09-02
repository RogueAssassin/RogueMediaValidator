# Installation

RogueMediaValidator is designed to run beside qBittorrent, Radarr and Sonarr on a shared private container network.

## Ports

The application listens internally on TCP 7811. The host mapping is controlled by `RMV_HTTP_PORT` and defaults to 7811.

## Podman

```bash
mkdir -p /opt/media-server/roguemediavalidator/data
cd /opt/media-server/roguemediavalidator
curl -fsSL https://raw.githubusercontent.com/RogueAssassin/roguemediavalidator/testing/compose.yaml -o compose.yaml
curl -fsSL https://raw.githubusercontent.com/RogueAssassin/roguemediavalidator/testing/.env.example -o .env
podman network inspect media-net >/dev/null 2>&1 || podman network create media-net
podman compose --env-file .env -f compose.yaml pull
podman compose --env-file .env -f compose.yaml up -d
```

## Docker

Use the same files with `docker compose`.

## First-run safety

Keep `RMV_DRY_RUN=true` until real qBittorrent metadata and decisions have been reviewed. Do not expose the RMV UI directly to the public Internet during testing.
