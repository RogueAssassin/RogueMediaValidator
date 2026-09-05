# Installation

RogueMediaValidator 0.6.x testing uses one `compose.yaml` for both Docker and Podman and supports guided browser setup for all common headless torrent clients.

## 1. Create the deployment

```bash
mkdir -p /opt/media-server/roguemediavalidator
cd /opt/media-server/roguemediavalidator

curl -fsSL https://raw.githubusercontent.com/RogueAssassin/roguemediavalidator/testing/compose.yaml -o compose.yaml
curl -fsSL https://raw.githubusercontent.com/RogueAssassin/roguemediavalidator/testing/.env.example -o .env
chmod 600 .env
```

Before starting RMV, edit the environment file:

```bash
nano .env
```

Confirm `RMV_IMAGE=ghcr.io/rogueassassin/roguemediavalidator:testing`, set `RMV_NETWORK` to the network shared with your torrent client, and keep `RMV_DRY_RUN=true` for initial validation. Save with **Ctrl+O**, press **Enter**, then exit with **Ctrl+X**.

Keep the torrent client blank for browser setup:

```env
RMV_TORRENT_CLIENT=
RMV_TORRENT_URL=
RMV_TORRENT_USERNAME=
RMV_TORRENT_PASSWORD=
```

Set the shared network and keep dry-run enabled:

```env
RMV_NETWORK=media-net
RMV_DRY_RUN=true
RMV_SETUP_UNLOCK=false
RMV_ADMIN_USERNAME=operator
RMV_ADMIN_PASSWORD=CHANGE-THIS-TO-A-STRONG-PASSWORD
```

## 2. Start RMV

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

## 3. Open Installation

Browse to:

```text
http://localhost:7811
```

Supported choices:

### qBittorrent

```text
http://qbittorrent:8080
```

Credentials: Web UI username/password.

Scope: categories.

Payload deletion through API: supported.

### Transmission

```text
http://transmission:9091/transmission/rpc
```

Credentials: optional HTTP Basic username/password.

Scope: labels.

Payload deletion through API: supported.

### Deluge

```text
http://deluge:8112/json
```

Credentials: Deluge Web UI password.

RMV logs into Deluge Web and connects to a configured daemon host when necessary.

Scope: Label plugin value when present, otherwise download location.

Payload deletion through API: supported.

### rTorrent / ruTorrent

```text
http://rutorrent/RPC2
```

Credentials: optional HTTP Basic credentials for the HTTP endpoint exposing XML-RPC.

Scope: `custom1` when present, otherwise torrent directory.

Payload deletion through normal XML-RPC: not guaranteed. RMV records a limited action when data deletion was requested.

### aria2

```text
http://aria2:6800/jsonrpc
```

Credentials: aria2 RPC secret goes in the password/secret field.

Scope: download directory.

Payload deletion through normal JSON-RPC: not guaranteed. RMV records a limited action when data deletion was requested.

## 4. Test before save

Installation requires a successful API test before Save & finish setup is enabled.

The test verifies:

- endpoint reachability;
- authentication;
- client version;
- scope discovery;
- provider data-deletion capability.

## 5. Scope bootstrap

Default:

```env
RMV_TORRENT_SCOPES=
RMV_TORRENT_AUTO_BOOTSTRAP_SCOPES=true
```

The first non-empty discovered provider scope set is persisted.

New scopes discovered later remain visible but unmanaged.

## 0.6.0 administrative Settings

Set both admin values in `.env` to enable the protected Settings page:

```env
RMV_ADMIN_USERNAME=operator
RMV_ADMIN_PASSWORD=CHANGE-THIS-TO-A-STRONG-PASSWORD
```

There is intentionally no default password. If either value is blank, `/settings` and `/api/admin/*` remain disabled.

After Installation has discovered the torrent client's categories, labels or download paths, open:

```text
http://YOUR-SERVER-IP:7811/settings
```

The browser will request the admin credentials. When `RMV_TORRENT_SCOPES` is blank, the Settings page can explicitly add or remove managed scopes. An empty selection is saved as a deliberate fail-closed state and is not automatically repopulated later.

If `RMV_TORRENT_SCOPES` is set in `.env`, environment ownership takes priority and the Settings page shows scopes as read-only.

## Advanced environment configuration

Skip browser setup with any supported provider ID:

```text
qbittorrent
transmission
deluge
rtorrent
aria2
```

Example:

```env
RMV_TORRENT_CLIENT=deluge
RMV_TORRENT_URL=http://deluge:8112/json
RMV_TORRENT_USERNAME=
RMV_TORRENT_PASSWORD=deluge-web-password
```

## Reconfiguring browser setup

Set:

```env
RMV_SETUP_UNLOCK=true
```

and recreate:

```bash
podman compose --env-file .env -f compose.yaml up -d --force-recreate
```

After changing provider settings, return `RMV_SETUP_UNLOCK=false` and recreate again.

## Applying .env changes

A normal restart does not reload container environment variables.

Use:

```bash
podman compose --env-file .env -f compose.yaml up -d --force-recreate
```

or the Docker equivalent.

Do not use `down -v` unless deleting RMV's database, setup state and audit history is intentional.

## Security

RMV does not mount Docker/Podman sockets.

Keep the setup interface private.

Credentials saved by browser setup stay in RMV's private data volume and are not returned through diagnostics.
