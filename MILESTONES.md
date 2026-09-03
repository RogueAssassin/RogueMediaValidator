# RogueMediaValidator milestones

## 0.1.x — Core validation

- strict payload validator ✅
- qBittorrent first integration ✅
- dry-run/enforcement ✅
- SQLite audit ✅

## 0.2.x — Operational safety

- policy fingerprints ✅
- structured action outcomes ✅
- single Docker/Podman Compose ✅
- SQLite hardening ✅

## 0.3.x — Scope automation and dashboard

- scope discovery/bootstrap ✅
- persisted scope isolation ✅
- simplified dashboard ✅

## 0.4.x — Multi-client foundation

- provider interface ✅
- browser Installation ✅
- qBittorrent ✅
- Transmission ✅
- setup test/lock ✅

## 0.5.x — Complete headless torrent-provider set

- Deluge ✅
- rTorrent / ruTorrent ✅
- aria2 ✅
- provider capability reporting ✅
- limited-delete auditing ✅
- removal of legacy qBittorrent compatibility code ✅
- all-provider CI regression tests ✅

### Remaining 0.5.x

- authenticated admin configuration
- UI-managed scope selection
- structured per-file reasons
- quarantine workflow
- post-download ffprobe/signature validation

## 0.6.x — Arr and Rogue ecosystem

- Radarr/Sonarr failed-download feedback
- retry/blacklist workflow
- source/indexer context
- notification/webhook events
- RogueDashboard integration
- Uptime Kuma/RogueDashboard health integration
- audit export/retention
