# Installation

RogueMediaValidator 0.2.x uses **one `compose.yaml` for both Docker and Podman**.

RMV runs beside qBittorrent on the shared private `media-net` network. The application listens internally on TCP 7811; `RMV_HTTP_PORT` controls only the host-side mapping.

## Files

```bash
mkdir -p /opt/media-server/roguemediavalidator
cd /opt/media-server/roguemediavalidator

curl -fsSL https://raw.githubusercontent.com/RogueAssassin/roguemediavalidator/testing/compose.yaml -o compose.yaml
curl -fsSL https://raw.githubusercontent.com/RogueAssassin/roguemediavalidator/testing/.env.example -o .env
chmod 600 .env
```

Edit `.env`, configure the qBittorrent endpoint/credentials, and keep `RMV_DRY_RUN=true` for first-run validation.

## Podman

```bash
podman network inspect media-net >/dev/null 2>&1 || podman network create media-net
podman compose --env-file .env -f compose.yaml config
podman compose --env-file .env -f compose.yaml pull
podman compose --env-file .env -f compose.yaml up -d
```

## Docker

```bash
docker network inspect media-net >/dev/null 2>&1 || docker network create media-net
docker compose --env-file .env -f compose.yaml config
docker compose --env-file .env -f compose.yaml pull
docker compose --env-file .env -f compose.yaml up -d
```

Both engines use the same managed named volume, `roguemediavalidator-data`, for `/data`. RMV itself runs as non-root UID 10001.

## Applying configuration changes

After editing `.env`, recreate the RMV container. Restarting an existing container does not reload environment variables.

Podman:

```bash
podman compose --env-file .env -f compose.yaml up -d --force-recreate
```

Docker:

```bash
docker compose --env-file .env -f compose.yaml up -d --force-recreate
```

`down` followed by `up -d` is also valid. Avoid `down -v` unless deleting RMV's database is intentional.

## First-run checks

```bash
curl -fsS http://127.0.0.1:7811/api/health
curl -fsS http://127.0.0.1:7811/api/diagnostics
```

Confirm qBittorrent connects, categories are discovered, and only explicitly configured categories enter scope.

## Upgrading from 0.1.x

0.1.x had a Podman-specific `compose.podman.yaml`. Delete that obsolete file after moving to 0.2.0; use only `compose.yaml`.

If the existing RMV named volume was created successfully under 0.1.x, it can be retained. The SQLite schema migrates automatically to add policy fingerprints and structured action outcome fields.

If an old test volume has broken ownership and contains no data you need, recreate only the RMV volume.

## First-run safety

Keep:

```env
RMV_DRY_RUN=true
```

until real qBittorrent metadata and decisions have been reviewed. Do not expose the RMV UI directly to the public Internet during testing.
