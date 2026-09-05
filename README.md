<div align="center">

<table>
  <tr>
    <td width="220" align="center">
      <img src="https://raw.githubusercontent.com/RogueAssassin/roguemediavalidator/main/app/static/icons/roguemediavalidator-approved-128.png" width="128" height="128" alt="RogueMediaValidator logo">
    </td>
    <td align="left">
      <h1>RogueMediaValidator</h1>
      <p><strong>Validate. Protect. Automate.</strong></p>
      <p>Multi-client pre-download torrent payload validation for Docker and Podman media stacks.</p>
    </td>
  </tr>
</table>

[![Release](https://img.shields.io/badge/RELEASE-0.5.0-42d6a4?style=for-the-badge&labelColor=45464d)](https://github.com/RogueAssassin/roguemediavalidator)
[![GHCR](https://img.shields.io/badge/GHCR-LATEST-5c6ac4?style=for-the-badge&logo=github&logoColor=white&labelColor=45464d)](https://github.com/RogueAssassin/roguemediavalidator/pkgs/container/roguemediavalidator)
[![CI](https://img.shields.io/github/actions/workflow/status/RogueAssassin/roguemediavalidator/ci.yml?branch=testing&style=for-the-badge&label=CI&labelColor=45464d)](https://github.com/RogueAssassin/roguemediavalidator/actions/workflows/ci.yml?query=branch%3Atesting)
[![Build](https://img.shields.io/github/actions/workflow/status/RogueAssassin/roguemediavalidator/container.yml?branch=testing&style=for-the-badge&label=BUILD&labelColor=45464d)](https://github.com/RogueAssassin/roguemediavalidator/actions/workflows/container.yml?query=branch%3Atesting)
![Engine](https://img.shields.io/badge/ENGINE-DOCKER%20%7C%20PODMAN-00cbe6?style=for-the-badge&labelColor=45464d)
![Platform](https://img.shields.io/badge/PLATFORM-AMD64%20%7C%20ARM64-42d6a4?style=for-the-badge&labelColor=45464d)

</div>

RogueMediaValidator (RMV) is a lightweight safety gate for automated torrent downloads. It reads torrent metadata from a supported torrent client, validates the declared payload before automation continues, stores every decision in SQLite, and can resume approved torrents or remove blocked torrents when enforcement is enabled.

The validation engine is provider-neutral. Every torrent application is isolated behind a small adapter that normalizes torrents, files, lifecycle states, validation scopes, resume operations, and removal operations into the same RMV model.

## Testing channel

This branch is the permanent development/testing channel for changes that are being validated before promotion to `main`.

Testing image:

```text
ghcr.io/rogueassassin/roguemediavalidator:testing
```

Use the `testing` branch deployment files together with the `:testing` image so the Compose file, environment example and application build stay on the same channel. For production media stacks, use the `main` branch and `:latest` image.

## Supported torrent clients

| Client | API | RMV scopes | Resume | Remove torrent | Remove payload data |
| --- | --- | --- | --- | --- | --- |
| qBittorrent | Web API | Categories | Yes | Yes | Yes |
| Transmission | RPC | Labels | Yes | Yes | Yes |
| Deluge | Web JSON-RPC | Label, otherwise download path | Yes | Yes | Yes |
| rTorrent / ruTorrent | XML-RPC | custom1 label, otherwise download path | Yes | Yes | No |
| aria2 | JSON-RPC | Download path | Yes | Yes | No |

This is the practical container/headless torrent-client set RMV targets. Desktop-only clients without a stable remotely controllable API are not advertised as supported.

Flood is a management UI rather than a torrent engine; configure RMV against the torrent client Flood controls.

## Why provider capabilities differ

Not every torrent API offers the same destructive operations.

qBittorrent, Transmission, and Deluge expose API calls that can remove both the torrent and local payload data.

The normal safe rTorrent XML-RPC and aria2 JSON-RPC paths can remove the torrent/task but do not provide a provider-neutral guarantee that the existing payload files are deleted.

RMV never pretends otherwise. If:

```env
RMV_DELETE_REJECTED_DATA=true
```

and the selected provider cannot guarantee data deletion, RMV removes the torrent entry and records:

```text
action=delete
action_status=limited
action_error=<provider cannot delete local payload data through supported API>
```

The dashboard includes limited actions in **Action issues**, and diagnostics expose `supports_delete_data`.

For strongest pre-download protection, have automation add new downloads paused/stopped so RMV can reject them before meaningful payload data exists.

## First-run Installation

A fresh install is designed to be safe and simple: create the deployment files, **edit the `.env` before starting RMV**, start the container, then finish the torrent-client connection through the browser.

For most media-server owners, leave the torrent-client connection fields blank in `.env` and use the guided Installation page. The important first-run values to review are the published port, container image, shared Docker/Podman network, and dry-run setting.

After the container starts, open:

```text
http://localhost:7811
```

RMV redirects to:

```text
/setup
```

The guided flow is:

```text
1. Select torrent client
2. Review provider-specific API URL and credential fields
3. Test connection
4. Read client version
5. Discover categories / labels / download paths
6. Confirm provider cleanup capability
7. Save configuration
8. Bootstrap the initial managed scopes
9. Enter the dashboard in dry-run mode
```

Setup locks after configuration. To intentionally reconfigure:

```env
RMV_SETUP_UNLOCK=true
```

recreate the container, make the change, then return the value to `false`.

## Default provider endpoints

These are container-network defaults and are editable in Installation:

```text
qBittorrent
http://qbittorrent:8080

Transmission
http://transmission:9091/transmission/rpc

Deluge
http://deluge:8112/json

rTorrent / ruTorrent
http://rutorrent/RPC2

aria2
http://aria2:6800/jsonrpc
```

The actual endpoint must be reachable **from inside the RMV container**.

## Authentication notes

### qBittorrent

Use the qBittorrent Web UI username/password.

### Transmission

Use optional HTTP Basic authentication if enabled by the Transmission deployment.

### Deluge

The password field is the Deluge Web UI password. RMV logs in through Deluge Web and automatically connects to the first configured daemon host when the Web UI is not already connected.

### rTorrent / ruTorrent

Use HTTP Basic credentials only when the reverse proxy exposing `RPC2` requires them.

RMV does not attempt direct SCGI socket mounting.

### aria2

Put the aria2 RPC secret in the **RPC secret** field. The username field is disabled.

RMV sends it as the JSON-RPC `token:<secret>` authorization parameter.

## Scope model

RMV calls provider-specific categories/labels/paths **scopes**.

Examples:

```text
qBittorrent
category=tv
        -> scopes=[tv]

Transmission
labels=[movies,4k]
        -> scopes=[movies,4k]

Deluge
label=tv
        -> scopes=[tv]

Deluge without a label
download_location=/downloads/tv
        -> scopes=[/downloads/tv]

rTorrent
custom1=movies
        -> scopes=[movies]

rTorrent without custom1
directory=/downloads/tv
        -> scopes=[/downloads/tv]

aria2
dir=/downloads/movies
        -> scopes=[/downloads/movies]
```

A torrent with several scopes enters RMV scope when **any** normalized scope matches the managed set.

## First-run scope bootstrap

Default:

```env
RMV_TORRENT_SCOPES=
RMV_TORRENT_AUTO_BOOTSTRAP_SCOPES=true
```

On the first successful non-empty discovery for a provider, RMV persists the discovered set and uses it as managed scope.

Later scopes are discovered but are not silently enrolled.

Bootstrap state is namespaced by provider, so qBittorrent categories cannot accidentally become Transmission labels or aria2 paths.

Explicit environment configuration overrides the persisted set:

```env
RMV_TORRENT_SCOPES=tv,movies
```

Use:

```env
RMV_TORRENT_SCOPES=*
```

only when every non-empty scope for the selected provider should be managed.

## One Compose file for Docker and Podman

RMV ships one:

```text
compose.yaml
```

for both engines.

External network:

```env
RMV_NETWORK=media-net
```

Set this to the network shared with the torrent client.

RMV does **not** mount Docker or Podman sockets and should never require:

```text
/var/run/docker.sock
/run/user/.../podman/podman.sock
```

## Quick install

The commands below create a clean RMV deployment in `/opt/media-server/roguemediavalidator`.

### 1. Download the deployment files

```bash
mkdir -p /opt/media-server/roguemediavalidator
cd /opt/media-server/roguemediavalidator

curl -fsSL https://raw.githubusercontent.com/RogueAssassin/roguemediavalidator/testing/compose.yaml -o compose.yaml
curl -fsSL https://raw.githubusercontent.com/RogueAssassin/roguemediavalidator/testing/.env.example -o .env
chmod 600 .env
```

### 2. Edit `.env` before the first start

**Do not skip this step.** Open the environment file:

```bash
nano .env
```

For a normal guided installation, check these settings:

```env
RMV_HTTP_PORT=7811
RMV_IMAGE=ghcr.io/rogueassassin/roguemediavalidator:testing
RMV_NETWORK=media-net
RMV_DRY_RUN=true

RMV_TORRENT_CLIENT=
RMV_TORRENT_URL=
RMV_TORRENT_USERNAME=
RMV_TORRENT_PASSWORD=
```

What to change:

- **`RMV_HTTP_PORT`** — change only if port `7811` is already in use.
- **`RMV_IMAGE`** — normally leave this unchanged; this README is configured for the **testing** channel.
- **`RMV_NETWORK`** — set this to the existing Docker/Podman network used by your torrent client. `media-net` is only the default.
- **`RMV_DRY_RUN=true`** — keep this enabled for the first install so RMV validates and records results without resuming or removing torrents.
- **Torrent client fields** — leave these four values blank when using the browser Installation wizard. Advanced users may fill them in to manage the provider entirely through environment variables.

In `nano`, save with **Ctrl+O**, press **Enter**, then exit with **Ctrl+X**.

### 3. Make sure the shared network exists

Use the **same network name you entered in `.env`**. If you kept the default `media-net`:

Podman:

```bash
podman network inspect media-net >/dev/null 2>&1 || podman network create media-net
```

Docker:

```bash
docker network inspect media-net >/dev/null 2>&1 || docker network create media-net
```

If your torrent client already uses another network, do not create `media-net`; set `RMV_NETWORK` to that existing network instead.

### 4. Pull and start RMV

Podman:

```bash
podman compose --env-file .env -f compose.yaml pull
podman compose --env-file .env -f compose.yaml up -d
```

Docker:

```bash
docker compose --env-file .env -f compose.yaml pull
docker compose --env-file .env -f compose.yaml up -d
```

### 5. Finish setup in the browser

Open:

```text
http://YOUR-SERVER-IP:7811
```

For a local install, `http://localhost:7811` also works.

Select your torrent client, enter its API/Web UI connection details, run **Test connection**, review discovered categories/labels/download paths, and save the setup.

Keep RMV in dry-run until Diagnostics shows the correct client, scopes and expected validation results. When you are satisfied, edit `.env` again with `nano .env`, set `RMV_DRY_RUN=false`, and recreate the container so enforcement becomes active.

## Advanced environment-managed setup

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

Environment configuration has precedence over browser-persisted provider configuration.

## Dry-run and enforcement

Default:

```env
RMV_DRY_RUN=true
```

Dry-run performs:

- provider connection;
- scope discovery;
- torrent enumeration;
- file-list validation;
- audit persistence;
- policy fingerprinting;
- diagnostics.

It does **not** resume or remove torrents.

Enforcement controls:

```env
RMV_AUTO_RESUME_VALID=true
RMV_REMOVE_REJECTED=true
RMV_DELETE_REJECTED_DATA=true
```

Actions are restricted to normalized download-lifecycle states:

```env
RMV_TORRENT_ACTION_STATES=pausedDL,stoppedDL,downloading,stalledDL,metaDL,queuedDL,checkingDL,forcedDL,allocating,checkingResumeData,moving
```

Completed/seeding/upload-only torrents are inspection-only.

## Default payload policy

Approved video:

```text
mkv mp4 m4v avi ts m2ts webm mov
```

Approved support:

```text
srt ass ssa sub idx nfo jpg jpeg png txt
```

Blocked:

```text
exe scr com bat cmd msi msix ps1 psm1 vbs vbe js jse wsf wsh lnk pif cpl jar apk dll
```

Minimum largest video:

```env
RMV_MIN_VIDEO_SIZE_MB=50
```

A torrent is blocked when a blocked file is present, no approved video exists, an unknown/unapproved file type exists, or the largest video is below the configured threshold.

## Policy fingerprinting

The active validation policy is fingerprinted from:

- video extensions;
- support extensions;
- blocked extensions;
- minimum video size.

When those rules change, an existing torrent hash is eligible for revalidation under the new policy.

## Persistence

SQLite stores:

- validation results;
- enforcement outcome;
- action errors;
- limited-action warnings;
- policy fingerprints;
- provider configuration;
- provider-specific managed scope bootstrap.

Container recreation keeps this state.

Do not use `compose down -v` unless intentionally deleting RMV setup/history.

## Dashboard

The dashboard focuses on:

- selected torrent client and version;
- connectivity;
- checked / approved / blocked totals;
- failed and limited action counts;
- managed and newly discovered scopes;
- current provider data-deletion capability;
- recent validation history;
- policy/runtime details.

## API

Read:

```text
GET /api/health
GET /api/diagnostics
GET /api/validations
GET /api/stats
GET /api/setup/providers
```

First-run/reconfiguration:

```text
POST /api/setup/test
POST /api/setup/save
```

The password/secret is never returned by diagnostics.

## Security boundary

RMV validates declared torrent metadata before download. It can detect dangerous filenames/extensions and malformed payload structure before downloading those files.

RMV is not an antivirus engine and cannot prove that an undownloaded file named `movie.mkv` actually contains valid video bytes.

Keep RMV and its selected torrent client on a trusted private network. Use HTTPS/authentication before exposing RMV beyond that boundary.

## Updating

Podman:

```bash
cd /opt/media-server/roguemediavalidator
podman compose --env-file .env -f compose.yaml pull
podman compose --env-file .env -f compose.yaml up -d
```

Docker:

```bash
docker compose --env-file .env -f compose.yaml pull
docker compose --env-file .env -f compose.yaml up -d
```

After changing `.env`, recreate:

```bash
podman compose --env-file .env -f compose.yaml up -d --force-recreate
```

or use the Docker equivalent.

## Next roadmap

With the provider layer complete, the next work moves above the client adapters:

- authenticated administrative settings;
- UI-managed scope selection;
- structured per-file reason detail;
- quarantine workflows;
- post-download ffprobe/signature validation;
- Radarr/Sonarr failed-download feedback;
- RogueDashboard integration;
- notification/webhook events;
- audit export/retention.

## Documentation

- [Installation](docs/INSTALL.md)
- [Testing](docs/TESTING.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Milestones](MILESTONES.md)
- [Changelog](CHANGELOG.md)
- [Security policy](SECURITY.md)

## License

MIT
