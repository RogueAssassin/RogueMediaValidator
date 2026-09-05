<div align="center">

<table>
  <tr>
    <td width="220" align="center">
      <img src="https://raw.githubusercontent.com/RogueAssassin/roguemediavalidator/main/app/static/icons/roguemediavalidator-approved-128.png" width="128" height="128" alt="RogueMediaValidator logo">
    </td>
    <td align="left">
      <h1>RogueMediaValidator</h1>
      <p><strong>Validate. Protect. Automate.</strong></p>
      <p>Provider-neutral torrent payload validation for Docker and Podman media stacks.</p>
    </td>
  </tr>
</table>

[![Release Candidate](https://img.shields.io/badge/RC-1.0.0-00cbe6?style=for-the-badge&labelColor=45464d)](https://github.com/RogueAssassin/roguemediavalidator/tree/testing)
[![CI](https://img.shields.io/github/actions/workflow/status/RogueAssassin/roguemediavalidator/ci.yml?branch=testing&style=for-the-badge&label=CI&labelColor=45464d)](https://github.com/RogueAssassin/roguemediavalidator/actions/workflows/ci.yml?query=branch%3Atesting)
[![Build](https://img.shields.io/github/actions/workflow/status/RogueAssassin/roguemediavalidator/container.yml?branch=testing&style=for-the-badge&label=BUILD&labelColor=45464d)](https://github.com/RogueAssassin/roguemediavalidator/actions/workflows/container.yml?query=branch%3Atesting)
![Engine](https://img.shields.io/badge/ENGINE-DOCKER%20%7C%20PODMAN-00cbe6?style=for-the-badge&labelColor=45464d)
![Platform](https://img.shields.io/badge/PLATFORM-AMD64%20%7C%20ARM64-42d6a4?style=for-the-badge&labelColor=45464d)

</div>

RogueMediaValidator (RMV) is a lightweight safety gate for automated torrent downloads. It validates declared torrent payloads before automation continues, stores decisions in SQLite, and can safely resume approved downloads, quarantine rejected downloads, or remove rejected torrents when enforcement is enabled.

The validation engine is provider-neutral. Torrent clients, media-automation systems, and notification targets are isolated behind adapters so the core policy is not tied to one application.

## Supported torrent clients

| Client | Scope source | Resume | Pause/hold | Remove torrent | Remove payload data |
| --- | --- | ---: | ---: | ---: | ---: |
| qBittorrent | Categories | Yes | Yes | Yes | Yes |
| Transmission | Labels | Yes | Yes | Yes | Yes |
| Deluge | Label or download path | Yes | Yes | Yes | Yes |
| rTorrent / ruTorrent | custom1 or download path | Yes | Yes | Yes | No |
| aria2 | Download path | Yes | Yes | Yes | No |

When a provider cannot guarantee local payload deletion, RMV records a limited action instead of reporting full deletion success.

## Key capabilities

- guided browser installation and connection testing;
- one shared Compose file for Docker and Podman;
- provider-neutral torrent validation;
- dry-run by default;
- managed-scope discovery with fail-closed behavior;
- authenticated Settings area;
- quarantine/hold support;
- Radarr and Sonarr automation feedback;
- generic media-automation webhooks;
- operational notification webhooks;
- audit history, export and retention;
- health, readiness and compact integration status endpoints;
- SQLite persistence across container recreation;
- no Docker or Podman socket mount required.

## Quick install

### 1. Create the deployment

```bash
mkdir -p /opt/media-server/roguemediavalidator
cd /opt/media-server/roguemediavalidator

curl -fsSL https://raw.githubusercontent.com/RogueAssassin/roguemediavalidator/testing/compose.yaml -o compose.yaml
curl -fsSL https://raw.githubusercontent.com/RogueAssassin/roguemediavalidator/testing/.env.example -o .env
chmod 600 .env
```

### 2. Edit `.env` before starting

The supplied `.env.example` is a fully commented administrator reference. It explains each setting, safe defaults, provider examples, and which values should normally be left unchanged.

```bash
nano .env
```

At minimum, review:

```env
RMV_IMAGE=ghcr.io/rogueassassin/roguemediavalidator:testing
RMV_HTTP_PORT=7811
RMV_NETWORK=media-net
RMV_DRY_RUN=true

RMV_ADMIN_USERNAME=operator
RMV_ADMIN_PASSWORD=CHANGE-THIS-TO-A-STRONG-PASSWORD

RMV_TORRENT_CLIENT=
RMV_TORRENT_URL=
RMV_TORRENT_USERNAME=
RMV_TORRENT_PASSWORD=
```

Use the same `RMV_NETWORK` as your torrent client. Leave the torrent-client fields blank for guided browser setup.

Save in nano with **Ctrl+O**, press **Enter**, then exit with **Ctrl+X**.

### 3. Start RMV

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

### 4. Finish setup

Open:

```text
http://YOUR-SERVER-IP:7811
```

Select the torrent client, enter its API/Web UI details, run **Test connection**, review discovered scopes, and save.

Keep `RMV_DRY_RUN=true` until Diagnostics and Settings show the correct provider, scopes and expected validation results. Then set `RMV_DRY_RUN=false` and recreate the container to enable enforcement.

## Optional integrations

Media automation:

```env
RMV_AUTOMATION_PROVIDERS_JSON='[{"provider":"radarr","name":"Movies","url":"http://radarr:7878","api_key":"RADARR-API-KEY"},{"provider":"sonarr","name":"TV","url":"http://sonarr:8989","api_key":"SONARR-API-KEY"}]'
```

Generic/custom automation:

```env
RMV_AUTOMATION_PROVIDERS_JSON='[{"provider":"webhook","name":"Custom automation","url":"http://automation:9000/rmv","token":"OPTIONAL-TOKEN"}]'
```

Operational notifications:

```env
RMV_NOTIFICATION_TARGETS_JSON='[{"provider":"webhook","name":"Ops","url":"http://notifications:9000/rmv","token":"OPTIONAL-TOKEN","events":["rejected","failed","limited","quarantined"]}]'
```

Supported notification events are `approved`, `rejected`, `failed`, `limited`, and `quarantined`.

## Monitoring

```text
GET /healthz
GET /readyz
GET /api/status
```

- `/healthz`: process liveness.
- `/readyz`: operational readiness; returns HTTP 503 until RMV has a successful client cycle and managed scopes.
- `/api/status`: compact no-secret status payload for RogueDashboard or other monitoring.

## Audit and retention

```env
RMV_AUDIT_RETENTION_DAYS=90
RMV_AUDIT_RETENTION_MAX_RECORDS=10000
```

Set either value to `0` to disable that limit.

Authenticated exports:

```text
GET /api/admin/audit/export.csv
GET /api/admin/audit/export.json
```

Audit cleanup does not remove provider setup, runtime settings, managed scopes, quarantine records, automation feedback, or notification history.

## Safety defaults

- `RMV_DRY_RUN=true` on first install;
- `RMV_SETUP_UNLOCK=false` during normal operation;
- no default admin password;
- unknown/unapproved payload extensions fail closed;
- newly discovered scopes are not silently enrolled after initial bootstrap;
- completed/seeding torrents remain inspection-only;
- Docker/Podman sockets are never required.

Do not use `compose down -v` unless deleting RMV's persistent database and setup state is intentional.

## Documentation

- [Installation](docs/INSTALL.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Security](SECURITY.md)
- [Changelog](CHANGELOG.md)

## License

See [LICENSE](LICENSE).
