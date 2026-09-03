<div align="center">

<table>
  <tr>
    <td width="220" align="center">
      <img src="https://raw.githubusercontent.com/RogueAssassin/roguemediavalidator/main/app/static/icons/roguemediavalidator-approved-128.png" width="128" height="128" alt="RogueMediaValidator logo">
    </td>
    <td align="left">
      <h1>RogueMediaValidator</h1>
      <p><strong>Validate. Protect. Automate.</strong></p>
      <p>Pre-download torrent payload validation for qBittorrent media automation.</p>
    </td>
  </tr>
</table>

[![Testing](https://img.shields.io/badge/TESTING-0.2.0-42d6a4?style=for-the-badge&labelColor=45464d)](https://github.com/RogueAssassin/roguemediavalidator/tree/testing)
[![GHCR](https://img.shields.io/badge/GHCR-TESTING-5c6ac4?style=for-the-badge&logo=github&logoColor=white&labelColor=45464d)](https://github.com/RogueAssassin/roguemediavalidator/pkgs/container/roguemediavalidator)
[![CI](https://img.shields.io/github/actions/workflow/status/RogueAssassin/roguemediavalidator/ci.yml?branch=testing&style=for-the-badge&label=CI&labelColor=45464d)](https://github.com/RogueAssassin/roguemediavalidator/actions/workflows/ci.yml?query=branch%3Atesting)
[![Build](https://img.shields.io/github/actions/workflow/status/RogueAssassin/roguemediavalidator/container.yml?branch=testing&style=for-the-badge&label=BUILD&labelColor=45464d)](https://github.com/RogueAssassin/roguemediavalidator/actions/workflows/container.yml?query=branch%3Atesting)
![Runtime](https://img.shields.io/badge/RUNTIME-PYTHON%203.12-ff4fc8?style=for-the-badge&labelColor=45464d)
![Engine](https://img.shields.io/badge/ENGINE-DOCKER%20%7C%20PODMAN-00cbe6?style=for-the-badge&labelColor=45464d)
![Platform](https://img.shields.io/badge/PLATFORM-AMD64%20%7C%20ARM64-42d6a4?style=for-the-badge&labelColor=45464d)

</div>

RogueMediaValidator (RMV) is a lightweight safety gate for qBittorrent-based media automation. It examines the torrent file list exposed by qBittorrent before an automated download is allowed to continue, applies a strict payload policy, records every decision in SQLite, and can optionally resume approved downloads or remove rejected ones.

RMV is intentionally independent of Radarr and Sonarr APIs in the current release. It scopes work by **qBittorrent categories**, so your category names do not need to be `radarr` and `sonarr`. If your download client uses `tv` and `movies`, configure exactly those names.

## Current testing release

**v0.2.0-testing** is the first operational-safety milestone. It keeps the proven category-discovery/fail-closed model and adds policy-aware revalidation, structured action outcomes, and a single Docker/Podman Compose deployment.

Testing image:

```text
ghcr.io/rogueassassin/roguemediavalidator:testing
```

Stable image remains:

```text
ghcr.io/rogueassassin/roguemediavalidator:latest
```

Do not assume the testing image is production-ready until your own qBittorrent workflow has been validated in dry-run mode.

## Why RMV exists

Automation normally trusts the release selected by an indexer/download pipeline. A release name can look legitimate even when its actual torrent payload contains unwanted or dangerous files. RMV validates the **file metadata qBittorrent receives for the torrent itself** rather than trusting the release name.

RMV currently checks:

- qBittorrent category scope.
- torrent state and whether an action is safe in that state.
- presence of at least one approved video file.
- blocked executable, installer and script extensions.
- unknown/unapproved extensions.
- minimum real-video file size.
- dry-run versus enforcement mode.
- previous validation/enforcement state.
- qBittorrent connectivity and version.
- configured versus discovered qBittorrent categories.

## Important security boundary

RMV is a **metadata validator**, not an antivirus engine.

Before a torrent downloads, qBittorrent can expose filenames and declared file sizes. RMV can therefore reject suspicious extensions, unexpected payload structure, missing video content and implausibly small media files before download.

RMV cannot inspect the actual bytes of a file that has not downloaded yet. It cannot prove that a file named `movie.mkv` contains valid video data or detect malware embedded inside an apparently legitimate media container. Future post-download validation could add MIME/signature/ffprobe inspection, but that is a separate security layer.

## Category model

RMV scopes torrents using the category reported by qBittorrent.

For the RogueGaming media stack:

```env
RMV_QB_CATEGORIES=tv,movies
```

Category matching is case-insensitive.

### Fail-closed behavior

An empty category list means **manage nothing**:

```env
RMV_QB_CATEGORIES=
```

This is deliberate. A missing environment variable must never silently expand RMV to every torrent.

To intentionally include every non-empty qBittorrent category:

```env
RMV_QB_CATEGORIES=*
```

Using `*` is not recommended for normal media automation because manual/non-media categories may then be inspected or actioned.

## Automatic category discovery

RMV retrieves qBittorrent's configured categories from:

```text
/api/v2/torrents/categories
```

Discovery does **not** automatically grant enforcement scope. It tells you what qBittorrent has configured so you can explicitly choose the categories RMV is allowed to manage.

After RMV has connected, inspect:

```bash
curl -s http://127.0.0.1:7811/api/diagnostics | python3 -m json.tool
```

Look for:

```json
"configured_categories": [
  "movies",
  "tv"
],
"discovered_categories": [
  "movies",
  "tv"
]
```

If qBittorrent contains additional categories, they will appear under `discovered_categories` but will remain out of scope unless added to `RMV_QB_CATEGORIES`.

The discovery cache refresh interval is controlled by:

```env
RMV_QB_CATEGORY_REFRESH_SECONDS=60
```

The application enforces a minimum effective refresh interval of 15 seconds.


## 0.2.0 policy-aware revalidation

RMV now calculates a short SHA-256 fingerprint from the active payload policy (approved video extensions, approved support extensions, blocked extensions, and minimum video size). The fingerprint is stored with every validation record and exposed through diagnostics.

If any of those validation rules change, an existing torrent hash is **not** treated as already validated under the new policy. RMV re-evaluates it automatically. This prevents stale decisions from surviving policy changes.

Validation history also records structured action state:

```text
action        none | resume | delete
action_status audit | not_required | inspection_only | success | failed
action_error  populated only when an action fails
```

A failed qBittorrent action is stored as failed and is not marked enforced, so RMV does not falsely claim that enforcement succeeded.

## Validation flow

```text
Radarr / Sonarr / other automation
              |
              v
         qBittorrent
              |
              | torrent metadata
              v
     RogueMediaValidator
              |
      category in scope?
          /       \
        no         yes
        |           |
     ignore     fetch files
                    |
              validate payload
               /          \
          approved        blocked
             |               |
        dry-run?          dry-run?
         /   \             /   \
       yes   no          yes    no
       |      |           |      |
     audit  resume*     audit   remove*
```

`*` Actions are still restricted by qBittorrent state and their corresponding settings.

## Inspection versus action

RMV deliberately separates **inspection** from **action**.

With:

```env
RMV_QB_INSPECT_ALL_STATES=true
```

every torrent in a configured category can be inspected when file metadata is available.

Actions are limited to:

```env
RMV_QB_ACTION_STATES=pausedDL,stoppedDL,downloading,stalledDL,metaDL,queuedDL,checkingDL,forcedDL,allocating,checkingResumeData,moving
```

Completed, uploading or seeding torrents can be audited but are not removed merely because they are found later in a non-download state.

For the strongest pre-download gate, configure your automation so newly added torrents arrive paused/stopped until RMV approves them.

## Dry-run mode

The default is:

```env
RMV_DRY_RUN=true
```

Dry-run performs discovery, inspection, validation, logging and database recording but does not resume or delete torrents.

Keep dry-run enabled until you have observed real `tv` and `movies` downloads and confirmed that RMV classifies them correctly.

Only then consider:

```env
RMV_DRY_RUN=false
```

## Enforcement settings

These settings only become effective when dry-run is disabled:

```env
RMV_AUTO_RESUME_VALID=true
RMV_REMOVE_REJECTED=true
RMV_DELETE_REJECTED_DATA=true
```

Behavior:

- approved paused/stopped downloads may be started when `RMV_AUTO_RESUME_VALID=true`.
- blocked torrents may be removed when `RMV_REMOVE_REJECTED=true`.
- their payload data may also be deleted when `RMV_DELETE_REJECTED_DATA=true`.
- torrents outside the configured action states are never deleted by RMV.

For the first enforcement test, consider temporarily setting:

```env
RMV_DELETE_REJECTED_DATA=false
```

until removal behavior has been confirmed.

## Default payload policy

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

A torrent is blocked when:

- it contains a blocked extension;
- it contains no approved video file;
- its largest approved video is below the configured minimum;
- or it contains an extension that is neither an approved video nor an approved supporting type.

A torrent containing both valid video and a blocked/unknown file still fails.

## qBittorrent connectivity

Default container-to-container endpoint:

```env
RMV_QB_URL=http://qbittorrent:8080
```

This must be the address reachable **from inside the RMV container**. It is not necessarily the host-published qBittorrent port.

Credentials:

```env
RMV_QB_USERNAME=admin
RMV_QB_PASSWORD=change-me
```

RMV accepts qBittorrent's standard successful `Ok.` login response and successful empty 2xx/204 responses. Expired sessions are authenticated again once automatically. Connection establishment uses bounded timeouts and connection retries rather than waiting indefinitely.

## Port model

RMV always listens on TCP **7811 inside the container**.

Host mapping:

```env
RMV_HTTP_PORT=7811
```

Default:

```text
host 7811 -> container 7811
```

The host port can change without changing the internal application port.

## Install with Docker or Podman

```bash
mkdir -p /opt/media-server/roguemediavalidator
cd /opt/media-server/roguemediavalidator

curl -fsSL https://raw.githubusercontent.com/RogueAssassin/roguemediavalidator/testing/compose.yaml -o compose.yaml
curl -fsSL https://raw.githubusercontent.com/RogueAssassin/roguemediavalidator/testing/.env.example -o .env

chmod 600 .env
nano .env
```

Set at minimum:

```env
RMV_QB_URL=http://qbittorrent:8080
RMV_QB_USERNAME=YOUR_USERNAME
RMV_QB_PASSWORD=YOUR_PASSWORD
RMV_QB_CATEGORIES=tv,movies
RMV_DRY_RUN=true
```

Then:

```bash
podman network inspect media-net >/dev/null 2>&1 || podman network create media-net
podman compose --env-file .env -f compose.yaml config
podman compose --env-file .env -f compose.yaml pull
podman compose --env-file .env -f compose.yaml up -d
```

RMV now ships one `compose.yaml` for both Docker and Podman. It uses a managed named volume and keeps the application running as non-root UID `10001`.

### Docker

Use the exact same `compose.yaml` with `docker compose`:

```bash
docker network inspect media-net >/dev/null 2>&1 || docker network create media-net
docker compose --env-file .env -f compose.yaml config
docker compose --env-file .env -f compose.yaml pull
docker compose --env-file .env -f compose.yaml up -d
```

## First-run verification

Check the container:

```bash
podman ps --filter name=roguemediavalidator
podman logs --tail 100 roguemediavalidator
```

Health:

```bash
curl -s http://127.0.0.1:7811/api/health | python3 -m json.tool
```

Diagnostics and category discovery:

```bash
curl -s http://127.0.0.1:7811/api/diagnostics | python3 -m json.tool
```

Recent validation history:

```bash
curl -s http://127.0.0.1:7811/api/validations | python3 -m json.tool
```

Statistics:

```bash
curl -s http://127.0.0.1:7811/api/stats | python3 -m json.tool
```

Dashboard:

```text
http://localhost:7811
```

## Health states

`/api/health` reports:

- `starting` before the first successful validation cycle;
- `healthy` after successful qBittorrent communication;
- `degraded` when the most recent cycle failed.

The container healthcheck intentionally checks that the RMV web process responds. A temporary qBittorrent outage should be surfaced as degraded diagnostics rather than causing the container engine to repeatedly restart a healthy RMV process.

## SQLite storage

Validation history is stored in:

```text
/data/rmv.db
```

RMV runs as non-root UID `10001`.

SQLite is configured with WAL journaling, a busy timeout and normal synchronous mode to reduce lock contention between the background validation loop and dashboard/API reads.

Do not delete the RMV data volume unless you intentionally want to remove validation history.

## API reference

### GET /api/health

High-level service health, qBittorrent connectivity, version, dry-run mode and last cycle details.

### GET /api/diagnostics

Operational diagnostics including:

- qBittorrent URL;
- qBittorrent connection state/version;
- configured categories;
- discovered qBittorrent categories;
- whether category scope is currently fail-closed;
- inspect/action state policy;
- torrent counters;
- storage statistics.

The endpoint never returns the qBittorrent password.

### GET /api/validations?limit=50

Recent validation records. Limit is clamped to 1-500.

### GET /api/stats

Validation totals for approved, blocked and handled/enforced records.

All current APIs are read-only.

## Rootless/container security

The supplied compose configuration uses:

```yaml
security_opt:
  - no-new-privileges:true
cap_drop:
  - ALL
```

The image runs as UID `10001`, not root.

RMV does not require the Docker or Podman socket and should never be given container-engine control.

During testing, keep port 7811 private to the host/LAN and do not expose RMV directly to the public Internet.

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

Your `.env` and named SQLite volume remain outside the image.

## Troubleshooting

### No torrents are being inspected

Check:

```bash
curl -s http://127.0.0.1:7811/api/diagnostics | python3 -m json.tool
```

Compare `configured_categories` with `discovered_categories`.

A blank `RMV_QB_CATEGORIES` is intentionally fail-closed.

### qBittorrent connection fails

Verify that `RMV_QB_URL` uses qBittorrent's internal container port on the shared network, then test DNS/network connectivity from the RMV container.

Also verify username/password and qBittorrent WebUI authentication settings.

### SQLite cannot open the database

RMV 0.2.0 uses one managed named volume for both Docker and Podman. If upgrading from an old test deployment with unusual ownership, recreate only the RMV container/volume after preserving any audit data you need.

### A legitimate release is blocked

Read the validation reason in the dashboard or `/api/validations`. Common causes are an unapproved support extension or a video smaller than `RMV_MIN_VIDEO_SIZE_MB`.

Do not simply add broad executable/archive extensions to the support allowlist. Adjust policy narrowly.

### RMV sees categories but ignores one

Discovery and permission are separate by design. Add the category explicitly to `RMV_QB_CATEGORIES`.

## Recommended live-testing sequence

1. Run `:testing` with `RMV_DRY_RUN=true`.
2. Confirm qBittorrent connection and version.
3. Confirm `discovered_categories` contains `tv` and `movies`.
4. Confirm `configured_categories` is exactly the set RMV should manage.
5. Submit known-good TV and movie torrents.
6. Confirm approved decisions without actions.
7. Test known-bad synthetic metadata through automated tests rather than deliberately downloading malware.
8. Restart RMV and confirm audit history persists.
9. Confirm qBittorrent outage/recovery behavior.
10. Temporarily use `RMV_DELETE_REJECTED_DATA=false` for the first enforcement test if desired.
11. Switch `RMV_DRY_RUN=false` only after classifications are correct.
12. Integrate RMV into the permanent media-server stack only after standalone behavior is proven.

## CI and release pipeline

Every push/PR to `main` and `testing` runs:

- Ruff static analysis;
- pytest regression tests;
- Python compile validation;
- Compose validation;
- container build.

The publish workflow builds Linux `amd64` and `arm64` images and publishes provenance and SBOM metadata.

Channels:

```text
testing branch -> :testing and :0.2.0-testing
main branch    -> :latest and the current stable version tag
git tag v*     -> matching tag metadata
```

## Current hardening priorities

The 0.1.x line established the safe validation gate. 0.2.0 now adds policy fingerprints and structured action outcomes. Remaining 0.2.x hardening includes:

- structured reason codes and complete per-file decision detail;
- optional quarantine workflows;
- explicit administrative API authentication before any write APIs are introduced;
- controlled policy editor/test mode;
- more detailed connection diagnostics;
- retention/backup controls for audit history;
- optional post-download media signature/ffprobe validation.

## Rogue ecosystem roadmap

Once standalone RMV validation is proven, RogueDashboard integration can consume RMV's read-only APIs for:

- health/status;
- dry-run/enforcement state;
- configured/discovered categories;
- approved/blocked counters;
- recent validation reasons.

This keeps RogueDashboard integration lightweight and avoids sharing the Docker/Podman socket.

## Documentation

Additional documentation:

- [Installation](docs/INSTALL.md)
- [Testing](docs/TESTING.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Milestones](MILESTONES.md)
- [Changelog](CHANGELOG.md)
- [Security policy](SECURITY.md)

## License

MIT
