<div align="center">

<table>
  <tr>
    <td width="220" align="center">
      <img src="https://raw.githubusercontent.com/RogueAssassin/roguemediavalidator/main/app/static/icons/roguemediavalidator-approved-128.png" width="128" height="128" alt="RogueMediaValidator logo">
    </td>
    <td align="left">
      <h1>RogueMediaValidator</h1>
      <p><strong>Validate. Protect. Automate.</strong></p>
      <p>Pre-download torrent payload validation for containerized media automation.</p>
    </td>
  </tr>
</table>

[![Testing](https://img.shields.io/badge/TESTING-0.4.0-42d6a4?style=for-the-badge&labelColor=45464d)](https://github.com/RogueAssassin/roguemediavalidator/tree/testing)
[![GHCR](https://img.shields.io/badge/GHCR-TESTING-5c6ac4?style=for-the-badge&logo=github&logoColor=white&labelColor=45464d)](https://github.com/RogueAssassin/roguemediavalidator/pkgs/container/roguemediavalidator)
[![CI](https://img.shields.io/github/actions/workflow/status/RogueAssassin/roguemediavalidator/ci.yml?branch=testing&style=for-the-badge&label=CI&labelColor=45464d)](https://github.com/RogueAssassin/roguemediavalidator/actions/workflows/ci.yml?query=branch%3Atesting)
[![Build](https://img.shields.io/github/actions/workflow/status/RogueAssassin/roguemediavalidator/container.yml?branch=testing&style=for-the-badge&label=BUILD&labelColor=45464d)](https://github.com/RogueAssassin/roguemediavalidator/actions/workflows/container.yml?query=branch%3Atesting)
![Engine](https://img.shields.io/badge/ENGINE-DOCKER%20%7C%20PODMAN-00cbe6?style=for-the-badge&labelColor=45464d)
![Platform](https://img.shields.io/badge/PLATFORM-AMD64%20%7C%20ARM64-42d6a4?style=for-the-badge&labelColor=45464d)

</div>

RogueMediaValidator (RMV) is a lightweight safety gate for automated torrent downloads. It reads torrent file metadata from a supported torrent client, validates the payload before allowing automation to continue, records every decision in SQLite, and can optionally resume approved torrents or remove rejected ones.

RMV is intentionally **torrent-client agnostic** from 0.4.0 onward. The validator core does not contain qBittorrent-specific logic; client adapters normalize each torrent application into the same internal model.

## Current testing release

**v0.4.0-testing** introduces the multi-client architecture and guided Installation page.

Testing image:

```text
ghcr.io/rogueassassin/roguemediavalidator:testing
```

## Supported torrent clients

| Client | Status | RMV scope model | Notes |
| --- | --- | --- | --- |
| qBittorrent | Supported | Categories | Native Web API, existing 0.3.x settings remain compatible |
| Transmission | Supported | Labels | Transmission 3.x/4.x RPC, modern JSON-RPC and legacy 4.0 protocol fallback |
| Deluge | Planned | Labels | Adapter planned for a following 0.4.x release |
| rTorrent / ruTorrent | Planned | Labels | Adapter planned after the setup workflow is proven |

Support means RMV can perform the operations required by the validator:

- connect/authenticate;
- read application version;
- enumerate torrents;
- discover categories or labels;
- retrieve torrent file metadata;
- normalize torrent lifecycle state;
- start/resume an approved torrent;
- remove a blocked torrent;
- optionally remove blocked payload data.

## Installation experience

Fresh 0.4.0 installations no longer require the user to know qBittorrent-specific environment variables.

Start RMV and open:

```text
http://localhost:7811
```

An unconfigured instance automatically redirects to:

```text
/setup
```

The setup flow is:

```text
1. Select torrent client
        |
        v
2. Enter API endpoint / credentials
        |
        v
3. Test connection
        |
        v
4. Discover categories / labels
        |
        v
5. Persist provider configuration
        |
        v
6. Start RMV dashboard in dry-run mode
```

The setup page offers sensible container-network defaults:

```text
qBittorrent
http://qbittorrent:8080

Transmission
http://transmission:9091/transmission/rpc
```

These are examples, not hard requirements. Use whatever DNS/service name and internal port are reachable from the RMV container.

## Docker and Podman

RMV deliberately does **not** inspect Docker or Podman sockets.

It does not need:

```text
/var/run/docker.sock
/run/user/.../podman/podman.sock
```

and those sockets should not be mounted into RMV.

Instead:

```text
RMV
 |
 | shared private container network
 |
 +--> qBittorrent API
 |
 +--> Transmission RPC
```

This gives Docker and Podman the same deployment path and keeps RMV least-privileged.

RMV continues to ship one:

```text
compose.yaml
```

for both engines. The external torrent-client network is configurable:

```env
RMV_NETWORK=media-net
```

Set that to the existing Docker/Podman network shared with the torrent client; no YAML edit is required.

## Quick install

```bash
mkdir -p /opt/media-server/roguemediavalidator
cd /opt/media-server/roguemediavalidator

curl -fsSL https://raw.githubusercontent.com/RogueAssassin/roguemediavalidator/testing/compose.yaml -o compose.yaml
curl -fsSL https://raw.githubusercontent.com/RogueAssassin/roguemediavalidator/testing/.env.example -o .env

chmod 600 .env
```

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

Then browse to port 7811 and complete Installation.

## Fresh-install environment

The default 0.4.0 environment intentionally leaves the torrent client blank:

```env
RMV_TORRENT_CLIENT=
RMV_TORRENT_URL=
RMV_TORRENT_USERNAME=
RMV_TORRENT_PASSWORD=
```

That enables browser setup.

Advanced users may skip the wizard by configuring a supported provider explicitly:

```env
RMV_TORRENT_CLIENT=qbittorrent
RMV_TORRENT_URL=http://qbittorrent:8080
RMV_TORRENT_USERNAME=admin
RMV_TORRENT_PASSWORD=change-me
```

or:

```env
RMV_TORRENT_CLIENT=transmission
RMV_TORRENT_URL=http://transmission:9091/transmission/rpc
RMV_TORRENT_USERNAME=
RMV_TORRENT_PASSWORD=
```

Environment configuration takes precedence over browser-persisted setup.

## Existing qBittorrent upgrades

Legacy 0.3.x variables remain supported:

```env
RMV_QB_URL=
RMV_QB_USERNAME=
RMV_QB_PASSWORD=
RMV_QB_CATEGORIES=
RMV_QB_AUTO_BOOTSTRAP_CATEGORIES=
RMV_QB_CATEGORY_REFRESH_SECONDS=
RMV_QB_INSPECT_ALL_STATES=
RMV_QB_ACTION_STATES=
```

An existing 0.3.x deployment therefore continues to start as qBittorrent without being forced into the Installation wizard.

New deployments should use the generic `RMV_TORRENT_*` settings or browser setup.

## Browser setup storage and lock

Browser setup stores the selected provider, endpoint, username, and password in RMV's private SQLite-backed data volume.

The password is never returned by diagnostics or setup-status responses.

After a client has been configured, setup writes are locked by default.

To intentionally reconfigure through the browser:

```env
RMV_SETUP_UNLOCK=true
```

then recreate the RMV container, make the configuration change, and return the value to:

```env
RMV_SETUP_UNLOCK=false
```

This prevents the normal dashboard from becoming an always-open credential-changing API.

## Scope model

Different torrent clients use different names for the same concept.

qBittorrent:

```text
categories
```

Transmission:

```text
labels
```

Internally RMV calls these **scopes**.

The generic configuration is:

```env
RMV_TORRENT_SCOPES=
RMV_TORRENT_AUTO_BOOTSTRAP_SCOPES=true
```

If scopes are blank, RMV performs the same safe one-time bootstrap introduced in 0.3.0:

```text
first successful discovery
        |
        v
persist discovered scopes
        |
        v
managed scopes
```

Later categories/labels are discovered but are not silently added to managed scope.

Explicit environment scopes always override persisted bootstrap values.

## qBittorrent behavior

qBittorrent exposes categories directly through its Web API.

A torrent with:

```text
category=tv
```

is normalized into:

```text
scopes=[tv]
```

The adapter continues to support qBittorrent v5 behavior used by the existing RMV test installation.

## Transmission behavior

Transmission uses torrent **labels** as RMV scopes.

A Transmission torrent may have multiple labels:

```text
labels=[movies, 4k]
```

RMV considers the torrent in scope when **any** torrent label intersects the managed scope set.

Transmission lifecycle states are normalized to the same RMV state names used by the validation service. Completed/seeding torrents remain inspection-only.

The Transmission adapter supports CSRF session-ID handling and optional HTTP Basic authentication.

## Validation policy

Approved video extensions:

```text
mkv mp4 m4v avi ts m2ts webm mov
```

Approved support extensions:

```text
srt ass ssa sub idx nfo jpg jpeg png txt
```

Blocked extensions:

```text
exe scr com bat cmd msi msix ps1 psm1 vbs vbe js jse wsf wsh lnk pif cpl jar apk dll
```

Minimum largest video size:

```env
RMV_MIN_VIDEO_SIZE_MB=50
```

A torrent is blocked if it contains a blocked file type, contains no approved video file, contains an unapproved/unknown file type, or its largest video is below the configured minimum.

The validation engine is shared by every torrent client adapter.

## Important security boundary

RMV validates **torrent metadata before download**.

It can detect:

- executable/script filenames;
- unwanted extensions;
- missing video payloads;
- suspiciously small declared media;
- unexpected file types.

It cannot prove that bytes which have not downloaded yet genuinely contain valid video.

Post-download MIME/signature/ffprobe validation remains a separate future layer.

## Dry-run and enforcement

The default remains:

```env
RMV_DRY_RUN=true
```

Dry-run performs connection, discovery, validation, logging and audit recording but does not resume or remove torrents.

Enforcement controls:

```env
RMV_AUTO_RESUME_VALID=true
RMV_REMOVE_REJECTED=true
RMV_DELETE_REJECTED_DATA=true
```

Actions remain restricted to normalized download-lifecycle states.

Completed, seeding, or upload-only torrents are audit-only.

## Policy fingerprinting

RMV calculates a policy fingerprint from:

- allowed video extensions;
- allowed support extensions;
- blocked extensions;
- minimum video size.

If the policy changes, existing torrent hashes are eligible for revalidation under the new policy.

## Dashboard

The operational dashboard is intentionally simple.

It shows:

- torrent client and version;
- connection state;
- validation totals;
- managed scopes;
- discovered-but-unmanaged scopes;
- torrent counts;
- recent validation history;
- action outcome;
- policy/runtime technical details.

The top bar includes:

```text
Installation
Diagnostics
```

rather than fake navigation tabs.

## API

Read APIs:

```text
GET /api/health
GET /api/diagnostics
GET /api/validations
GET /api/stats
GET /api/setup/providers
```

First-run setup APIs:

```text
POST /api/setup/test
POST /api/setup/save
```

Setup save locks after configuration unless `RMV_SETUP_UNLOCK=true`.

Credentials are excluded from diagnostics.

## Diagnostics

`/api/diagnostics` now has a generic:

```json
"torrent_client": {
  "provider": "qbittorrent",
  "display_name": "qBittorrent",
  "connected": true,
  "version": "v5.2.3",
  "scope_name": "categories",
  "managed_scopes": ["radarr", "tv"],
  "discovered_scopes": ["radarr", "tv"]
}
```

A limited `qbittorrent` compatibility block remains temporarily for existing integrations.

New integrations should consume `torrent_client`.

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

If `.env` changes, recreate the container:

```bash
podman compose --env-file .env -f compose.yaml up -d --force-recreate
```

or use the Docker equivalent.

Do not use `down -v` unless RMV database/history/setup state is intentionally being deleted.

## 0.4.x roadmap

After the qBittorrent + Transmission base is proven:

- Deluge adapter;
- rTorrent/ruTorrent adapter;
- authenticated administrative settings;
- editable managed scopes from the UI;
- provider-specific connection diagnostics;
- structured per-file failure details;
- optional quarantine workflows;
- post-download media verification;
- RogueDashboard integration.

## Documentation

- [Installation](docs/INSTALL.md)
- [Testing](docs/TESTING.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Milestones](MILESTONES.md)
- [Changelog](CHANGELOG.md)
- [Security policy](SECURITY.md)

## License

MIT
