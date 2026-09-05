# Installation

RogueMediaValidator uses one `compose.yaml` for both Docker and Podman.

## 1. Create the deployment

```bash
mkdir -p /opt/media-server/roguemediavalidator
cd /opt/media-server/roguemediavalidator

curl -fsSL https://raw.githubusercontent.com/RogueAssassin/roguemediavalidator/testing/compose.yaml -o compose.yaml
curl -fsSL https://raw.githubusercontent.com/RogueAssassin/roguemediavalidator/testing/.env.example -o .env
chmod 600 .env
```

## 2. Edit the environment file

Do this before the first start. The generated `.env` contains comments explaining every supported administrator setting and its safe/default behavior.

```bash
nano .env
```

Recommended first-run values:

```env
RMV_IMAGE=ghcr.io/rogueassassin/roguemediavalidator:testing
RMV_HTTP_PORT=7811
RMV_NETWORK=media-net
RMV_DRY_RUN=true
RMV_QUARANTINE_REJECTED=false

RMV_ADMIN_USERNAME=operator
RMV_ADMIN_PASSWORD=CHANGE-THIS-TO-A-STRONG-PASSWORD

RMV_TORRENT_CLIENT=
RMV_TORRENT_URL=
RMV_TORRENT_USERNAME=
RMV_TORRENT_PASSWORD=
```

Use the network already shared by the torrent client. Leave the torrent-client values blank to use the browser Installation wizard.

Save with **Ctrl+O**, press **Enter**, then exit with **Ctrl+X**.

## 3. Start RMV

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

If you use a different shared network, set `RMV_NETWORK` to that name and do not create `media-net`.

## 4. Complete browser setup

Open:

```text
http://YOUR-SERVER-IP:7811
```

Choose a supported torrent client:

| Client | Typical container endpoint | Credentials |
| --- | --- | --- |
| qBittorrent | `http://qbittorrent:8080` | Web UI username/password |
| Transmission | `http://transmission:9091/transmission/rpc` | Optional HTTP Basic auth |
| Deluge | `http://deluge:8112/json` | Deluge Web password |
| rTorrent / ruTorrent | `http://rutorrent/RPC2` | Optional HTTP Basic auth |
| aria2 | `http://aria2:6800/jsonrpc` | RPC secret |

The endpoint must be reachable from inside the RMV container.

Run **Test connection** before saving. RMV verifies reachability, authentication, client version, scope discovery, and payload-deletion capability.

## 5. Verify scopes and dry-run

Fresh installs default to:

```env
RMV_TORRENT_SCOPES=
RMV_TORRENT_AUTO_BOOTSTRAP_SCOPES=true
RMV_DRY_RUN=true
```

The first non-empty discovered scope set is persisted. Later newly discovered scopes remain visible but are not silently enrolled.

Open **Settings** with the admin credentials and verify the managed scopes.

When Diagnostics and Settings look correct:

```bash
nano .env
```

Set:

```env
RMV_DRY_RUN=false
```

Then recreate the container:

```bash
podman compose --env-file .env -f compose.yaml up -d --force-recreate
```

Use the Docker equivalent when applicable.

## Quarantine

Optional hold behavior:

```env
RMV_QUARANTINE_REJECTED=true
```

When enabled, rejected actionable torrents are paused/stopped and recorded as held instead of being removed.

Review held items from the dashboard or:

```text
GET /api/quarantine
```

## Media automation

Radarr/Sonarr example:

```env
RMV_AUTOMATION_PROVIDERS_JSON='[{"provider":"radarr","name":"Movies","url":"http://radarr:7878","api_key":"RADARR-API-KEY"},{"provider":"sonarr","name":"TV","url":"http://sonarr:8989","api_key":"SONARR-API-KEY"}]'
```

Generic automation webhook:

```env
RMV_AUTOMATION_PROVIDERS_JSON='[{"provider":"webhook","name":"Custom automation","url":"http://automation:9000/rmv","token":"OPTIONAL-TOKEN"}]'
```

Use **Settings → Test integrations** after recreation.

## Operational notifications

```env
RMV_NOTIFICATION_TARGETS_JSON='[{"provider":"webhook","name":"Ops","url":"http://notifications:9000/rmv","token":"OPTIONAL-TOKEN","events":["rejected","failed","limited","quarantined"]}]'
```

Use **Settings → Test notifications** to send an `rmv.test` event.

## Monitoring

```text
/healthz
/readyz
/api/status
```

Use `/healthz` for liveness and `/readyz` when the monitor should fail unless RMV is fully operational.

## Audit retention

```env
RMV_AUDIT_RETENTION_DAYS=90
RMV_AUDIT_RETENTION_MAX_RECORDS=10000
```

Set either to `0` to disable that limit.

Authenticated exports are available at:

```text
/api/admin/audit/export.csv
/api/admin/audit/export.json
```

## Advanced environment-managed provider setup

Browser setup can be skipped:

```env
RMV_TORRENT_CLIENT=qbittorrent
RMV_TORRENT_URL=http://qbittorrent:8080
RMV_TORRENT_USERNAME=admin
RMV_TORRENT_PASSWORD=secret
```

Supported provider IDs:

```text
qbittorrent
transmission
deluge
rtorrent
aria2
```

Environment configuration takes precedence over browser-persisted provider configuration.

## Backup, upgrade and rollback

RMV keeps its persistent state in the named `roguemediavalidator-data` volume. Before an upgrade or rollback, stop RMV and back up that volume with your Docker/Podman volume-backup method.

Do not remove the volume during a normal upgrade. Pull the new image and recreate the container while keeping the same volume.

For rollback, restore the saved volume if the newer release performed a database change that is not compatible with the older image. Keep a backup until the upgraded instance has completed a successful client cycle and `/readyz` returns HTTP 200.

## Reconfiguration

To intentionally unlock browser setup:

```env
RMV_SETUP_UNLOCK=true
```

Recreate RMV, make the change, then return it to:

```env
RMV_SETUP_UNLOCK=false
```

and recreate again.

## Applying .env changes

A normal restart does not reload container environment variables. Recreate the container after changing `.env`.

Do not use `down -v` unless deleting RMV setup state, history, and persistent data is intentional.

## Security

RMV does not mount Docker or Podman sockets. Keep the UI on a trusted network, use a strong admin password, and place HTTPS/authentication in front of RMV if it is exposed beyond that network.
