# Testing RogueMediaValidator

Use the permanent `testing` branch and `ghcr.io/rogueassassin/roguemediavalidator:testing`.

## 0.3.0 validation sequence

1. Use only `compose.yaml` with Docker Compose or Podman Compose.
2. Start with a fresh RMV data volume for a true first-install bootstrap test.
3. Configure qBittorrent credentials and keep `RMV_DRY_RUN=true`.
4. Set `RMV_QB_CATEGORIES=` and `RMV_QB_AUTO_BOOTSTRAP_CATEGORIES=true`.
5. Start RMV and confirm the first non-empty discovered category set is persisted and becomes `managed_categories`.
6. Confirm `category_source=auto_bootstrap` and `category_bootstrap_complete=true`.
7. Restart/recreate RMV without deleting the data volume and confirm the managed set persists.
8. Add a new qBittorrent category after bootstrap; confirm it appears in `discovered_categories` but not `managed_categories`.
9. Set an explicit `RMV_QB_CATEGORIES` value and recreate RMV; confirm `category_source=environment` and the explicit set overrides bootstrap.
10. Clear the explicit value again and recreate RMV; confirm the persisted bootstrap set resumes control.
11. Disable `RMV_QB_AUTO_BOOTSTRAP_CATEGORIES` on a fresh data volume with blank categories and confirm scope remains empty.
12. Re-run the 0.2.0 policy fingerprint and structured action-outcome regression checks.
13. Confirm SQLite history survives restart/recreation.

## Environment changes require container recreation

After changing `.env`:

```bash
podman compose --env-file .env -f compose.yaml up -d --force-recreate
```

or use the equivalent `docker compose` command. A plain container restart keeps the old environment.

## CI gates

Every push/PR to `main` or `testing` must pass:

- Ruff
- pytest
- Python compile validation
- single `compose.yaml` configuration validation
- container build

The testing branch publishes `:testing` and `:0.3.0-testing`.
