# Testing RogueMediaValidator

Use the permanent `testing` branch and `ghcr.io/rogueassassin/roguemediavalidator:testing` image for development validation.

## Safe validation sequence

1. Copy `.env.example` to `.env`.
2. Configure qBittorrent credentials and keep `RMV_DRY_RUN=true`.
3. Keep RMV's internal port at 7811. Change only `RMV_HTTP_PORT` if the host port must move.
4. Start RMV on the same private container network as qBittorrent.
5. Add a known-good paused media torrent and confirm it is reported as approved.
6. Add synthetic/bad metadata in automated tests and confirm executable, unknown, missing-video and undersized-video cases are blocked.
7. Review the dashboard and `/api/health`.
8. Only after live decisions are correct, set `RMV_DRY_RUN=false`.

## CI gates

Every push/PR to `main` or `testing` must pass:

- Ruff static checks
- pytest policy tests
- Python compile validation
- Compose configuration validation
- container build

The container workflow publishes amd64/arm64 images. The `testing` branch publishes `:testing` and `:0.1.0-testing`; `main` publishes `:latest` and `:0.1.0`.
