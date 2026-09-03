# Installation

RogueMediaValidator 0.4.x uses one `compose.yaml` for both Docker and Podman and supports browser-based torrent-client setup.

## 1. Create the deployment

```bash
mkdir -p /opt/media-server/roguemediavalidator
cd /opt/media-server/roguemediavalidator

curl -fsSL https://raw.githubusercontent.com/RogueAssassin/roguemediavalidator/testing/compose.yaml -o compose.yaml
curl -fsSL https://raw.githubusercontent.com/RogueAssassin/roguemediavalidator/testing/.env.example -o .env
chmod 600 .env
```

The fresh 0.4.0 environment leaves `RMV_TORRENT_CLIENT` blank so the Installation page is used.

Set the external network shared with the torrent client, then keep dry-run enabled:

```env
RMV_NETWORK=media-net
RMV_DRY_RUN=true
RMV_SETUP_UNLOCK=false
```

If your torrent client uses a different external network name, change only `RMV_NETWORK`; the compose file does not need editing.

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

RMV runs as non-root UID 10001 and uses a named volume for `/data`.

## 3. Open Installation

Browse to:

```text
http://localhost:7811
```

An unconfigured instance redirects to:

```text
/setup
```

Choose a supported provider.

### qBittorrent

Suggested container-network endpoint:

```text
http://qbittorrent:8080
```

RMV uses qBittorrent categories as scopes.

### Transmission

Suggested endpoint:

```text
http://transmission:9091/transmission/rpc
```

RMV uses Transmission torrent labels as scopes.

Transmission HTTP Basic authentication is optional and may be left blank if the RPC service does not require it.

## 4. Test before save

The wizard requires a successful connection test before Save & finish setup becomes available.

The connection test retrieves the client version and current scopes.

The final save persists the provider configuration to the RMV data volume and loads the client immediately.

## 5. Scope bootstrap

With:

```env
RMV_TORRENT_SCOPES=
RMV_TORRENT_AUTO_BOOTSTRAP_SCOPES=true
```

the first non-empty discovered category/label set is persisted as managed scope.

New scopes discovered later remain visible but unmanaged.

## Advanced environment configuration

To skip browser setup:

```env
RMV_TORRENT_CLIENT=qbittorrent
RMV_TORRENT_URL=http://qbittorrent:8080
RMV_TORRENT_USERNAME=admin
RMV_TORRENT_PASSWORD=secret
```

or:

```env
RMV_TORRENT_CLIENT=transmission
RMV_TORRENT_URL=http://transmission:9091/transmission/rpc
RMV_TORRENT_USERNAME=
RMV_TORRENT_PASSWORD=
```

Environment configuration takes precedence over browser-persisted setup.

## Existing 0.3.x qBittorrent installs

Legacy `RMV_QB_*` settings remain supported. Existing deployments can pull 0.4.0 without rewriting their current qBittorrent environment immediately.

## Reconfiguring browser setup

Setup writes lock after configuration.

To intentionally unlock:

```env
RMV_SETUP_UNLOCK=true
```

Then recreate:

```bash
podman compose --env-file .env -f compose.yaml up -d --force-recreate
```

Make the change at `/setup`, then set the unlock back to false and recreate again.

## Applying .env changes

A normal container restart does not reload changed environment variables.

Use:

```bash
podman compose --env-file .env -f compose.yaml up -d --force-recreate
```

or the Docker equivalent.

Do not add `-v` unless deleting the RMV database, setup state and audit history is intentional.

## Security model

RMV does not need access to Docker or Podman sockets.

Do not mount a container-engine socket into RMV.

Browser-stored client credentials remain in the private RMV data volume and are not returned through diagnostics APIs.

Keep RMV on a trusted/private network while testing.
