# Architecture

RogueMediaValidator 0.4.x separates torrent-client integration from payload validation.

```text
Radarr / Sonarr / other automation
              |
              v
      supported torrent client
       /                 \
qBittorrent           Transmission
 categories              labels
       \                 /
        \               /
         provider adapter
              |
              v
      normalized torrent
      + normalized files
      + normalized states
      + normalized scopes
              |
              v
       validation engine
        /             \
   approved           blocked
      |                  |
 resume when safe    remove when safe
        \             /
         audit/action store
              |
              v
      dashboard + API
```

## Provider interface

Every torrent client adapter implements the same logical operations:

- report provider/application version;
- discover validation scopes;
- enumerate torrents;
- fetch file metadata for a torrent;
- normalize lifecycle state;
- resume/start an approved torrent;
- remove a blocked torrent and optionally its local data.

The validation service therefore does not need to understand qBittorrent Web API objects, Transmission RPC objects, or future provider-specific structures.

## Scopes

RMV uses the generic term **scope**.

Provider mappings:

```text
qBittorrent  -> category
Transmission -> label
```

A provider may expose more than one scope on a torrent. Transmission, for example, can return multiple labels. A torrent enters RMV scope when any of its normalized scopes intersects the managed-scope set.

## First-run setup

A fresh install may start without a provider.

```text
/
 |
 +--> no provider configured
        |
        v
      /setup
        |
        +--> select provider
        +--> enter endpoint/credentials
        +--> connection test
        +--> scope discovery
        +--> persist provider config
        |
        v
     dashboard
```

Provider configuration created by browser setup is stored in the RMV data volume. Environment configuration overrides browser setup.

Setup writes lock after initial configuration unless explicitly unlocked.

## Container boundary

RMV never needs Docker/Podman API/socket access.

The only required communication path is:

```text
RMV container -> selected torrent client API
```

Both containers must therefore share a network with working service-name/IP routing.

This preserves the same architecture under Docker and Podman.

## Validation and action safety

The provider adapter normalizes client-specific states into RMV lifecycle states. The service decides whether a torrent can be actioned.

Inspection may occur in all states when configured, but destructive actions remain limited to normalized download-lifecycle states.

Completed, seeding, and upload-only torrents are audit-only.

## Persistence

SQLite stores:

- validation decisions;
- action outcomes;
- policy fingerprints;
- provider setup configuration;
- provider-specific bootstrap scopes.

Bootstrap scopes are namespaced per provider so switching from qBittorrent to Transmission does not incorrectly reuse qBittorrent categories as Transmission labels.

## Compatibility

0.4.x keeps legacy qBittorrent settings and compatibility diagnostics while new integrations migrate to the generic torrent-client model.
