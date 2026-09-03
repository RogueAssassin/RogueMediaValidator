# Testing RogueMediaValidator

Use the permanent `testing` branch and `ghcr.io/rogueassassin/roguemediavalidator:testing`.

## 0.2.0 validation sequence

1. Use only `compose.yaml` with either Docker Compose or Podman Compose.
2. Start with a fresh or known-good RMV data volume.
3. Configure qBittorrent credentials and keep `RMV_DRY_RUN=true`.
4. Leave `RMV_QB_CATEGORIES=` blank first and confirm categories are discovered but no torrents enter scope.
5. Explicitly configure the intended categories, such as `tv,movies`.
6. Confirm known-good media validates as approved and blocked/unknown payload tests fail closed.
7. Record the current `policy_fingerprint` from `/api/diagnostics`.
8. Change a validation rule, such as `RMV_MIN_VIDEO_SIZE_MB`, restart RMV, and confirm the fingerprint changes and existing in-scope torrents can be revalidated.
9. In controlled enforcement testing, confirm successful resume/delete actions record `action_status=success`.
10. Simulate an action failure and confirm it is stored as `action_status=failed` without being marked enforced.
11. Confirm SQLite history survives container restart/recreation.
12. Only after those checks pass should permanent stack integration begin.

## CI gates

Every push/PR to `main` or `testing` must pass:

- Ruff
- pytest
- Python compile validation
- single `compose.yaml` configuration validation
- container build

The testing branch publishes `:testing` and `:0.2.0-testing`.
