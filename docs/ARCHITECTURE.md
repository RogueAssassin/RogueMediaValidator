# Architecture

RogueMediaValidator 0.5.x uses a provider-neutral validation core.

```text
                    +--> qBittorrent Web API
                    |
                    +--> Transmission RPC
                    |
Automation -> torrent client adapter -> normalized RMV model -> validator
                    |
                    +--> Deluge Web JSON-RPC
                    |
                    +--> rTorrent XML-RPC
                    |
                    +--> aria2 JSON-RPC
```

Every provider adapter must expose:

- version;
- scopes;
- torrents;
- files;
- resume;
- delete;
- `supports_delete_data`.

## Normalized torrent model

Provider-specific data is converted into:

```text
hash
name
_scopes[]
state
```

The validator never needs provider-specific API objects.

## Scope mapping

```text
qBittorrent  -> categories
Transmission -> labels
Deluge       -> label, fallback download_location
rTorrent     -> custom1, fallback directory
aria2        -> dir
```

## State mapping

Providers normalize their own lifecycle states into RMV states such as:

```text
stoppeddl
downloading
queueddl
checkingdl
uploading
stoppedup
```

The shared action-state policy then decides whether resume/delete is allowed.

## Data-deletion capability

Provider adapters declare:

```text
supports_delete_data = true | false
```

True:

```text
qBittorrent
Transmission
Deluge
```

False:

```text
rTorrent / ruTorrent
aria2
```

When data deletion is requested but unsupported, RMV removes the torrent entry, records a limited action, preserves the warning in SQLite, and never claims full payload deletion occurred.

## Setup

```text
unconfigured
   |
   v
/setup
   |
   +--> provider selection
   +--> provider-specific endpoint/credentials
   +--> connection test
   +--> capability discovery
   +--> scope discovery
   +--> save
   |
   v
dashboard
```

Setup persists in the RMV data volume and locks after configuration.

## Container boundary

RMV talks only to the selected torrent application's API.

Docker/Podman sockets are intentionally excluded.

## Persistence

SQLite stores:

- setup configuration;
- provider-specific scope bootstrap;
- validation decisions;
- action status;
- action error/warning;
- policy fingerprint.

## Source layout

```text
app/clients/base.py
app/clients/factory.py
app/clients/qbittorrent.py
app/clients/transmission.py
app/clients/deluge.py
app/clients/rtorrent.py
app/clients/aria2.py

app/service.py
app/validator.py
app/store.py
app/main.py
```

There is no longer a separate qBittorrent compatibility service module.
