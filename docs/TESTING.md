# Testing RogueMediaValidator

Use the permanent `testing` branch and `ghcr.io/rogueassassin/roguemediavalidator:testing`.

## 0.7.0 quarantine and hold test plan

Every supported provider must pass:

1. Installation selector is enabled.
2. Suggested API URL is correct for the provider.
3. Provider-specific credential labels are correct.
4. Test connection succeeds against a real deployment.
5. Version is detected.
6. Scopes are discovered.
7. Setup saves and locks.
8. Managed scopes persist across container recreation.
9. Torrent metadata is normalized.
10. File metadata reaches the shared validator.
11. Approved stopped downloads resume when enforcement is enabled.
12. With quarantine disabled, blocked actionable torrents follow the existing removal behavior.
13. With `RMV_QUARANTINE_REJECTED=true`, blocked actionable torrents are paused/stopped and are not removed.
14. Held torrents appear in `/api/quarantine` and the dashboard count.
15. Quarantine records preserve provider, scope and rejection reason.
16. Completed/seeding torrents stay inspection-only.

## qBittorrent

Verify:

- Web UI login/session recovery;
- categories;
- v5 start/stop endpoints;
- delete with optional data deletion.

## Transmission

Verify:

- CSRF session-ID negotiation;
- modern JSON-RPC;
- legacy RPC fallback;
- labels and multi-label matching;
- torrent start/stop/remove;
- local data removal.

## Deluge

Verify:

- Web UI login;
- already-connected daemon path;
- automatic host connection when Web UI is disconnected;
- label scope;
- download-location fallback scope;
- file retrieval;
- pause/resume;
- remove with data.

## rTorrent / ruTorrent

Verify:

- XML-RPC endpoint;
- optional HTTP Basic auth;
- client version;
- `d.multicall2`;
- `custom1` label;
- directory fallback;
- `f.multicall`;
- `d.start` / `d.stop`;
- `d.erase`;
- requested payload deletion records `action_status=limited`.

## aria2

Verify:

- JSON-RPC secret token;
- BitTorrent-only filtering;
- active/waiting/stopped enumeration;
- download-directory scopes;
- file metadata;
- `aria2.pause` / `aria2.unpause`;
- `aria2.remove`;
- requested payload deletion records `action_status=limited`.

## Shared regressions

- executable/script blocking;
- unknown extension fail-closed behavior;
- policy fingerprint revalidation;
- dry-run safety;
- scope bootstrap isolation;
- no silent new-scope enrolment;
- failed action persistence;
- limited-action persistence;
- quarantine persistence and opt-in precedence;
- explicit empty UI scope remains fail-closed;
- setup password not returned by diagnostics;
- template render tests;
- one Docker/Podman Compose file;
- configurable external network;
- container build on amd64/arm64.

## CI gates

Every push to `testing`/main must pass:

- Ruff;
- pytest;
- Python compile;
- Compose validation;
- container build.

Testing publishes:

```text
:testing
:0.7.0-testing
```
