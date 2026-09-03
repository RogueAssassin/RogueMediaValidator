# Testing RogueMediaValidator

Use the permanent `testing` branch and `ghcr.io/rogueassassin/roguemediavalidator:testing`.

## 0.4.0 test plan

### Existing qBittorrent upgrade

1. Keep the existing 0.3.x `RMV_QB_*` environment.
2. Pull/recreate 0.4.0.
3. Confirm the dashboard loads instead of redirecting to Installation.
4. Confirm provider is qBittorrent.
5. Confirm existing category bootstrap state remains intact.
6. Confirm the known blocked `.exe` audit remains in SQLite.
7. Confirm dry-run/enforcement behavior remains unchanged.

### Fresh qBittorrent wizard

1. Start with a fresh RMV volume and fresh 0.4.0 `.env`.
2. Confirm `/` redirects to `/setup`.
3. Select qBittorrent.
4. Enter the internal API endpoint and credentials.
5. Confirm Test connection reports version and categories.
6. Save.
7. Confirm setup redirects to dashboard.
8. Confirm categories bootstrap and persist.
9. Confirm setup becomes locked.

### Fresh Transmission wizard

1. Start with a fresh RMV volume.
2. Select Transmission.
3. Use the RPC endpoint reachable from RMV.
4. Test authentication/CSRF handling.
5. Confirm Transmission version is displayed.
6. Confirm torrent labels are discovered.
7. Save and verify the label set bootstraps.
8. Confirm a torrent with any managed label enters scope.
9. Confirm a multi-label torrent is in scope when at least one label is managed.
10. Confirm stopped/downloading states are actionable and seeding is inspection-only.
11. Confirm file metadata is normalized into the shared validator.
12. Keep `RMV_DRY_RUN=true` for the first live client test.

### Setup security

1. Complete browser setup.
2. Confirm a second save request is rejected while `RMV_SETUP_UNLOCK=false`.
3. Set `RMV_SETUP_UNLOCK=true`, recreate, and confirm reconfiguration is available.
4. Return unlock to false after the test.
5. Confirm diagnostics never expose the password.

### Provider isolation

1. Bootstrap qBittorrent scopes.
2. Switch to Transmission.
3. Confirm the qBittorrent bootstrap set does not become Transmission's label set.
4. Switch back and confirm provider-specific scope persistence.

### Regression gates

Re-run:

- executable/script blocking;
- unknown-extension fail-closed behavior;
- policy fingerprint revalidation;
- dry-run safety;
- action outcome recording;
- qBittorrent outage recovery;
- SQLite persistence;
- single Docker/Podman Compose validation.

## Environment changes

After changing `.env`, recreate RMV:

```bash
podman compose --env-file .env -f compose.yaml up -d --force-recreate
```

A plain restart keeps the old environment.

## CI gates

Every testing/main push must pass:

- Ruff;
- pytest;
- dashboard/setup template render tests;
- qBittorrent adapter tests;
- Transmission adapter tests;
- Python compile validation;
- `compose.yaml` validation;
- container build.

Testing publishes:

```text
:testing
:0.4.0-testing
```
