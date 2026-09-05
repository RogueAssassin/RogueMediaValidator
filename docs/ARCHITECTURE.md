# Architecture

RogueMediaValidator uses a provider-neutral core.

```text
Torrent client API
      |
      v
Torrent adapter -> normalized torrent/file model -> validation policy
                                                   |
                     +-----------------------------+------------------+
                     |                             |                  |
                     v                             v                  v
               enforcement                  automation feedback   notifications
                     |                             |                  |
                     v                             v                  v
             torrent provider              Radarr/Sonarr/webhook   webhook targets
                     |
                     v
                  SQLite
```

## Torrent-client adapters

Every torrent adapter exposes the common operations required by the core:

- version;
- scopes;
- torrents;
- files;
- pause;
- resume;
- delete;
- payload-deletion capability.

Supported adapters:

```text
qBittorrent
Transmission
Deluge
rTorrent / ruTorrent
aria2
```

Provider-specific metadata is normalized before it reaches the validator.

## Scope mapping

```text
qBittorrent  -> categories
Transmission -> labels
Deluge       -> label, fallback download_location
rTorrent     -> custom1, fallback directory
aria2        -> dir
```

Scope ownership is explicit. Environment configuration has priority, UI-managed scopes are persisted, and automatic bootstrap occurs only once.

## Enforcement

The validation result is persisted before optional integrations run.

Approved actionable downloads may be resumed. Rejected actionable downloads can be quarantined or removed. Providers that cannot guarantee local payload deletion record a limited action rather than full success.

Completed/seeding/upload-only torrents remain inspection-only.

## Media automation

Media automation is separate from torrent enforcement.

Radarr and Sonarr are adapters, not core dependencies. Generic webhooks provide a universal integration path for other TV/movie automation systems.

Automation feedback failures are isolated from the validation/enforcement decision.

## Notifications

Operational notifications are best-effort and run after the validation outcome is known. Notification delivery failures are audited separately and cannot alter a torrent decision.

## Persistence

SQLite stores:

- provider setup;
- managed-scope state;
- validation decisions;
- enforcement outcomes and errors;
- quarantine records;
- automation feedback;
- notification delivery history;
- runtime settings.

Validation history can be exported and pruned without deleting runtime/provider configuration.

## Operational endpoints

```text
/healthz    liveness
/readyz     readiness
/api/status compact integration status
```

## Container boundary

RMV communicates only with configured application APIs.

Docker and Podman sockets are intentionally excluded, and the container drops Linux capabilities with `no-new-privileges`.

## Source layout

```text
app/clients/         torrent-client adapters
app/automation/      media-automation adapters
app/notifications/   notification targets
app/validator.py     payload policy
app/service.py       validation/enforcement orchestration
app/store.py         SQLite persistence
app/main.py          web UI and API
```
