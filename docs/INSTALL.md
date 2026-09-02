# Installation

RogueMediaValidator is designed to run beside qBittorrent, Radarr and Sonarr on a shared private container network.

## Ports

The application listens internally on TCP 7811. The host mapping is controlled by `RMV_HTTP_PORT` and defaults to 7811.

## Podman

RMV uses a managed named volume for SQLite data. The Podman-specific compose adds the `:U` ownership option so the volume is writable by RMV's non-root UID 10001 under rootless Podman.

```bash
mkdir -p /opt/media-server/roguemediavalidator
cd /opt/media-server/roguemediavalidator

curl -fsSL https://raw.githubusercontent.com/RogueAssassin/roguemediavalidator/testing/compose.podman.yaml -o compose.podman.yaml
curl -fsSL https://raw.githubusercontent.com/RogueAssassin/roguemediavalidator/testing/.env.example -o .env

podman network inspect media-net >/dev/null 2>&1 || podman network create media-net
podman compose --env-file .env -f compose.podman.yaml pull
podman compose --env-file .env -f compose.podman.yaml up -d
```

Check startup:

```bash
podman ps --filter name=roguemediavalidator
podman logs --tail=100 roguemediavalidator
curl -fsS http://127.0.0.1:${RMV_HTTP_PORT:-7811}/api/health
```

## Docker

Use `compose.yaml`. Docker uses the same managed named volume without Podman's `:U` ownership flag.

## Upgrading from the initial testing compose

The original testing compose used `./data:/data`. On rootless Podman that directory can be unwritable by RMV's non-root UID and produce `sqlite3.OperationalError: unable to open database file`.

For the initial testing release, stop/remove the failed container and start with the Podman compose above. The managed volume is called `roguemediavalidator_roguemediavalidator-data` (the exact prefix may vary by compose provider).

## First-run safety

Keep `RMV_DRY_RUN=true` until real qBittorrent metadata and decisions have been reviewed. Do not expose the RMV UI directly to the public Internet during testing.
