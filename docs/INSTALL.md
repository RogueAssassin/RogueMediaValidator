# Installation

RogueMediaValidator 0.3.x uses **one `compose.yaml` for both Docker and Podman**.

RMV runs beside qBittorrent on the shared private `media-net` network. The application listens internally on TCP 7811; `RMV_HTTP_PORT` controls only the host-side mapping.

## Files

```bash
mkdir -p /opt/media-server/roguemediavalidator
cd /opt/media-server/roguemediavalidator

curl -fsSL https://raw.githubusercontent.com/RogueAssassin/roguemediavalidator/testing/compose.yaml -o compose.yaml
curl -fsSL https://raw.githubusercontent.com/RogueAssassin/roguemediavalidator/testing/.env.example -o .env
chmod 600 .env
```

Configure the qBittorrent endpoint and credentials. For the default first-run category automation, leave:

```env
RMV_QB_CATEGORIES=
RMV_QB_AUTO_BOOTSTRAP_CATEGORIES=true
RMV_DRY_RUN=true
```

On the first successful qBittorrent category discovery, RMV persists the current non-empty category set into SQLite and uses it immediately as managed scope. The container does not rewrite your `.env`.

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

Both engines use the same managed named volume for `/data`. RMV runs as non-root UID 10001.

## First-run category verification

```bash
curl -fsS http://127.0.0.1:7811/api/diagnostics | python3 -m json.tool
```

A successful default bootstrap should show:

```json
"environment_categories": [],
"managed_categories": ["movies", "tv"],
"discovered_categories": ["movies", "tv"],
"category_source": "auto_bootstrap",
"category_auto_bootstrap": true,
"category_bootstrap_complete": true
```

New categories discovered after that bootstrap are shown but are **not** automatically added to managed scope.

To explicitly control scope instead:

```env
RMV_QB_CATEGORIES=tv,movies
```

Explicit environment categories always override the persisted bootstrap set.

To leave a blank scope fail-closed:

```env
RMV_QB_CATEGORIES=
RMV_QB_AUTO_BOOTSTRAP_CATEGORIES=false
```

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

A full `down` followed by `up -d` is also valid. Avoid `down -v` unless deleting RMV's database and persisted category bootstrap is intentional.

## Upgrading from 0.2.0

Existing 0.2.0 data volumes can be retained. 0.3.0 creates the `runtime_settings` table automatically.

If your existing `.env` already contains `RMV_QB_CATEGORIES=tv,movies`, those explicit categories continue to win. To test 0.3.0 auto-bootstrap, clear `RMV_QB_CATEGORIES`, keep `RMV_QB_AUTO_BOOTSTRAP_CATEGORIES=true`, and recreate the container.

## First-run safety

Keep `RMV_DRY_RUN=true` until the bootstrapped managed categories and validation decisions have been reviewed. Do not expose RMV directly to the public Internet during testing.
