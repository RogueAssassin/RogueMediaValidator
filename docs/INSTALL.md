# Installation

RogueMediaValidator uses one `compose.yaml` for Docker and Podman and follows the same deployment pattern as RogueDashboard and RogueForge.

## 1. Create the deployment

```bash
mkdir -p /opt/media-server/roguemediavalidator
cd /opt/media-server/roguemediavalidator

curl -fsSL https://raw.githubusercontent.com/RogueAssassin/RogueMediaValidator/main/compose.yaml -o compose.yaml
curl -fsSL https://raw.githubusercontent.com/RogueAssassin/RogueMediaValidator/main/.env.example -o .env
curl -fsSL https://raw.githubusercontent.com/RogueAssassin/RogueMediaValidator/main/update.sh -o update.sh
chmod 600 .env
chmod +x update.sh
```

## 2. Edit the environment file

```bash
nano .env
```

For a first install, keep:

```env
RMV_IMAGE=ghcr.io/rogueassassin/roguemediavalidator:latest
RMV_HTTP_PORT=7811
RMV_NETWORK=media-net
RMV_DRY_RUN=true
RMV_SETUP_UNLOCK=false

RMV_ADMIN_USERNAME=
RMV_ADMIN_PASSWORD=

RMV_TORRENT_CLIENT=
RMV_TORRENT_URL=
RMV_TORRENT_USERNAME=
RMV_TORRENT_PASSWORD=
```

Set a strong administrator username/password before exposing Settings. Leave the torrent-client values blank to use browser setup.

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

If your torrent client uses another shared network, set `RMV_NETWORK` to that network instead.

## 4. Complete browser setup

Open:

```text
http://YOUR-SERVER-IP:7811
```

Choose a provider and use its container-reachable API/Web UI address.

| Client | Typical endpoint | Credentials |
| --- | --- | --- |
| qBittorrent | `http://qbittorrent:8080` | Web UI username/password |
| Transmission | `http://transmission:9091/transmission/rpc` | Optional HTTP Basic auth |
| Deluge | `http://deluge:8112/json` | Deluge Web password |
| rTorrent / ruTorrent | `http://rutorrent/RPC2` | Optional HTTP Basic auth |
| aria2 | `http://aria2:6800/jsonrpc` | RPC secret |

Run **Test connection**, confirm the discovered scopes and save.

## 5. Validate before enabling enforcement

Fresh installs use:

```env
RMV_TORRENT_SCOPES=
RMV_TORRENT_AUTO_BOOTSTRAP_SCOPES=true
RMV_DRY_RUN=true
```

Verify Diagnostics and Settings before changing:

```env
RMV_DRY_RUN=false
```

Recreate RMV after any `.env` change:

```bash
podman compose --env-file .env -f compose.yaml up -d --force-recreate
```

Use the Docker equivalent when applicable.

## Updating

Stable production:

```bash
cd /opt/media-server/roguemediavalidator
./update.sh latest
```

Pinned production release:

```bash
./update.sh 1.1.1
```

Testing channel:

```bash
./update.sh testing
```

The updater preserves the existing `.env` and named `roguemediavalidator-data` volume, backs up deployment files to `backups/update/` (the last ten are kept), verifies the pulled/running image and checks `/healthz` before completing.

It pulls the requested image before changing any deployment file, so an unpublished tag leaves the installation untouched. If the recreated container fails verification or its health check, the previous `compose.yaml`, `.env` and image are restored automatically.

`compose.yaml` is replaced on every update. Keep local changes in `compose.override.yaml`; the updater applies it and never overwrites it.

`compose.yaml` uses `pull_policy: missing` so the container can be recreated while the registry is unreachable. Run `./update.sh` to move to a newer image, or set `RMV_PULL_POLICY=always` to pull on every recreate.

## Monitoring

```text
/healthz
/readyz
/api/status
```

Use `/healthz` for process liveness and `/readyz` when monitoring should fail until RMV is configured, connected and managing scopes.

## Persistent data and rollback

RMV stores persistent state in the named `roguemediavalidator-data` volume.

Do not use `compose down -v` for a normal upgrade. Back up the volume before a release that changes the database contract, and retain that backup until the upgraded instance has completed a successful client cycle.

## Reconfiguration

To intentionally unlock browser provider setup:

```env
RMV_SETUP_UNLOCK=true
```

Recreate RMV, make the change, then return the setting to `false` and recreate again.

## Security

RMV does not mount Docker or Podman sockets. The container runs unprivileged with all capabilities dropped, `no-new-privileges`, a read-only root filesystem and a bounded writable `/tmp`.

Keep the UI on a trusted network and use HTTPS/authentication if it is exposed beyond that network.
