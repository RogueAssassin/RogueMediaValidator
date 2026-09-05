# Installation

RogueMediaValidator 0.9.x testing uses one `compose.yaml` for both Docker and Podman and supports guided browser setup for all common headless torrent clients.

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
RMV_QUARANTINE_REJECTED=false
RMV_AUTOMATION_PROVIDERS_JSON=
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

## 0.7.0 quarantine testing

Quarantine is opt-in and should first be tested with dry-run still enabled:

```env
RMV_DRY_RUN=true
RMV_QUARANTINE_REJECTED=true
```

After confirming the correct provider and managed scopes, enforcement can be enabled by setting `RMV_DRY_RUN=false` and recreating the container.

When quarantine is enabled, blocked actionable torrents are paused/stopped and retained instead of deleted. Review held items at:

```text
http://YOUR-SERVER-IP:7811/api/quarantine
```

The dashboard also reports the current held count. Set `RMV_QUARANTINE_REJECTED=false` to return to the existing removal behavior.

## 0.8.0 universal media automation

The automation layer is optional and supports multiple instances. Configure it in `.env`.

Radarr + Sonarr example:

```env
RMV_AUTOMATION_PROVIDERS_JSON='[{"provider":"radarr","name":"Movies","url":"http://radarr:7878","api_key":"RADARR-API-KEY"},{"provider":"sonarr","name":"TV","url":"http://sonarr:8989","api_key":"SONARR-API-KEY"}]'
```

Separate Sonarr/Radarr instances can be added as additional objects in the same array.

For another/custom TV or movie automation system, use the generic webhook provider:

```env
RMV_AUTOMATION_PROVIDERS_JSON='[{"provider":"webhook","name":"Custom automation","url":"http://automation:9000/rmv","token":"OPTIONAL-TOKEN"}]'
```

After editing `.env`, recreate RMV, open **Settings**, and use **Test integrations**.

Radarr/Sonarr feedback matches the torrent hash against the upstream queue `downloadId`. RMV requests upstream blocklisting/retry handling but uses `removeFromClient=false`, keeping the torrent-client action under RMV control.

Automation feedback is only sent after a rejected torrent has an RMV enforcement outcome such as a successful delete, limited delete, or quarantine hold. Provider failures are audited and isolated.

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
