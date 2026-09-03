# RogueMediaValidator milestones

## 0.1.x — Core validation and safe discovery

- qBittorrent metadata inspection ✅
- strict payload allow/block policy ✅
- dry-run and controlled enforcement ✅
- SQLite audit history ✅
- Docker/Podman container base ✅

## 0.2.x — Operational safety

- policy fingerprint revalidation ✅
- structured action outcomes/failure visibility ✅
- one Docker/Podman `compose.yaml` ✅
- SQLite WAL/busy timeout ✅

## 0.3.x — Scope automation and dashboard

- qBittorrent category discovery ✅
- one-time first-run scope bootstrap ✅
- persistent managed scope ✅
- no silent permission expansion ✅
- simplified operational dashboard ✅

## 0.4.x — Multi-client platform

- provider-neutral torrent client interface ✅
- browser Installation/setup workflow ✅
- qBittorrent adapter ✅
- Transmission adapter ✅
- provider-specific scope persistence ✅
- setup connection test and post-install lock ✅
- Deluge adapter
- rTorrent / ruTorrent adapter
- authenticated administrative configuration
- UI-managed scope selection after bootstrap
- structured per-file reason detail
- configurable quarantine workflow
- optional post-download ffprobe/signature validation

## 0.5.x — Arr and Rogue ecosystem

- optional Radarr/Sonarr failed-download feedback
- retry/blacklist workflow
- source/indexer context
- notification/webhook events
- native RogueDashboard status/health integration
- recent validation widgets
- shared deployment helpers
- Uptime Kuma/RogueDashboard health integration without container socket access
