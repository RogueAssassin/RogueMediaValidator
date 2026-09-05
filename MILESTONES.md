# RogueMediaValidator roadmap

RogueMediaValidator is moving from a provider-complete validator in 0.5.x toward a release-ready media safety service in 1.0.0.

The permanent `testing` branch is where each milestone is developed and validated. Features should only move to `main` after their milestone is stable, upgrade-safe, documented, and covered by regression tests.

## Completed foundation

### 0.1.x — Core validation ✅
- strict torrent payload validation
- qBittorrent integration
- dry-run and enforcement modes
- SQLite audit history

### 0.2.x — Operational safety ✅
- validation policy fingerprints
- structured enforcement outcomes
- shared Docker/Podman Compose deployment
- SQLite hardening and migrations

### 0.3.x — Scope automation and dashboard ✅
- scope discovery and one-time bootstrap
- persisted scope isolation
- simplified operational dashboard

### 0.4.x — Multi-client foundation ✅
- provider-neutral torrent-client interface
- guided browser Installation
- qBittorrent and Transmission adapters
- setup testing and configuration lock

### 0.5.x — Headless torrent-provider coverage ✅
- Deluge
- rTorrent / ruTorrent
- aria2
- provider capability reporting
- limited-delete auditing
- legacy qBittorrent compatibility cleanup
- all-provider regression coverage

---

## 0.6.0 — Administration and operator control ✅

**Goal:** make RMV comfortable to operate day-to-day without requiring routine `.env` editing.

Validated foundation:
- authenticated administrative/settings area
- UI-managed scope selection after initial discovery
- add/remove managed scopes without silently enrolling new discoveries
- clear environment-vs-persisted configuration ownership
- explicit fail-closed empty scope selection
- provider-neutral regression coverage retained
- refreshed README and Installation documentation

Carried into the 0.7.x operator-review work:
- structured per-file validation reasons
- improved validation history filtering/detail
- safer destructive-action confirmation and review workflows
- deeper migration/recovery coverage

**0.6.0 exit criteria:**
- fresh Docker and Podman installs pass
- upgrades from 0.5.0 preserve configuration/history
- every supported torrent provider still passes regression tests
- no administrative secret is exposed by diagnostics/API
- scope changes cannot accidentally broaden enforcement
- CI and container builds pass on testing

## 0.7.0 — Quarantine and deep media validation — validated quarantine foundation

**Goal:** move beyond torrent filename/metadata policy into optional post-download media verification.

Implemented in first 0.7.0 testing slice:
- provider-neutral pause/stop capability for all supported torrent clients
- opt-in quarantine workflow for rejected actionable payloads
- persistent quarantine audit records and dashboard/API visibility
- quarantine precedence over deletion only when explicitly enabled

Next:
- quarantine workflow for suspicious/post-download payloads
- configurable quarantine behavior and retention
- optional post-download ffprobe validation
- media/container signature checks where practical
- distinguish pre-download metadata validation from post-download content validation
- structured quarantine reasons and lifecycle states
- retry/recheck workflow after policy changes or operator review
- disk/path safety checks and bounded processing
- UI visibility for quarantined and rechecked items

**Exit criteria:** deep validation is opt-in, bounded, auditable, and cannot silently delete data outside configured RMV behavior.

## 0.8.0 — Universal media automation feedback ✅

**Goal:** let RMV participate cleanly in automated TV/movie acquisition workflows without coupling the core integration model to Radarr or Sonarr.

Planned:
- provider-neutral media-automation adapter/interface
- Radarr integration as a first-class movie provider
- Sonarr integration as a first-class TV provider
- support for additional TV/movie automation applications through the same adapter model
- generic webhook/API integration path for compatible or custom automation systems
- capability discovery so RMV only attempts actions supported by each automation provider
- failed-download/rejection feedback
- retry, blocklist or equivalent rejection workflow where supported
- source/indexer context attached to validation records when exposed by the provider
- correlation between torrent, automation download and RMV decision
- safe handling when one or more automation services are unavailable
- multiple automation-provider instances where practical
- integration diagnostics and connection-test actions
- duplicate/retry loop protection
- keep torrent-provider validation independent from the automation provider selected

**Architecture rule:** Radarr and Sonarr must not become hard-coded assumptions in RMV core. Automation integrations should follow the same provider-neutral philosophy used for torrent clients so future TV/movie managers can be added without rewriting validation logic.

**Exit criteria:** a rejected download can be reported to any supported upstream automation provider without creating uncontrolled retry loops, coupling RMV to the Arr ecosystem, or breaking standalone RMV operation.

## 0.9.0 — Notifications, ecosystem and operations — active testing

**Goal:** make RMV observable and easy to integrate into a complete media stack.

Planned:
- notification/webhook events for approved, rejected, failed and limited actions
- RogueDashboard integration
- health/status integration suitable for Uptime Kuma and similar monitors
- audit export
- configurable audit retention/cleanup
- operational metrics and clearer health/readiness reporting
- backup/restore guidance for RMV persistent state
- UI/UX accessibility and responsive-layout pass
- performance profiling for large torrent histories and busy clients

**Exit criteria:** integrations are optional, failures are isolated, and long-running installations remain maintainable.

## 0.9.x — Release-candidate hardening

**Goal:** freeze major features and prove the 1.0 contract.

Planned:
- no new major features after feature freeze
- complete Docker and Podman clean-install matrix
- upgrade testing from supported pre-1.0 releases
- all-provider live/regression validation
- database migration and recovery testing
- security review of authentication, credentials and destructive actions
- dependency and container-image review
- API/configuration compatibility review
- documentation audit from a first-time media-owner perspective
- troubleshooting and recovery procedures
- release candidate images/tags
- fix-only RC cycle until release gates pass

## 1.0.0 — Production release

**Goal:** declare the first stable, documented and supportable RogueMediaValidator contract.

Release requirements:
- qBittorrent, Transmission, Deluge, rTorrent/ruTorrent and aria2 provider support verified
- Docker and Podman installation verified
- safe first-run wizard and dry-run defaults
- authenticated administration
- UI-managed scopes
- clear validation reasons and audit trail
- optional quarantine/deep validation
- stable provider-neutral TV/movie automation feedback integrations, including Radarr and Sonarr
- optional notifications and Rogue ecosystem integration
- documented backup, restore, upgrade and rollback paths
- stable configuration/API behavior documented
- clean CI/container builds for release commit
- release notes and migration guide completed
- no known critical data-loss, authentication or enforcement defects

After 1.0.0, breaking configuration/API changes should be reserved for future major versions; 1.x development should prefer backwards-compatible features and migrations.
