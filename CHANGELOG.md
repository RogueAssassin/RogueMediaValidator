# Changelog

## 0.1.0 - Testing

- Initial RogueMediaValidator implementation.
- Added strict torrent payload inspection against video/support allowlists.
- Added hard rejection for executable and scripting extensions.
- Added minimum video size validation and fail-closed unknown extension handling.
- Added qBittorrent authentication, torrent/file inspection, resume and delete actions.
- Added dry-run mode as the safe default.
- Added persistent SQLite validation history.
- Added responsive Rogue-style dashboard and health/stats/activity APIs.
- Added hardened non-root container image and Docker/Podman compose definitions.
- Added CI tests, Ruff validation and multi-architecture GHCR publishing workflow.
