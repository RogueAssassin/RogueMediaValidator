# Testing Guide

1. Configure qBittorrent and leave `RMV_DRY_RUN=true`.
2. Ensure Radarr/Sonarr automated torrents arrive paused.
3. Test a normal media torrent and verify RMV records `approved` without changing it.
4. Test a controlled fixture/mocked torrent containing a blocked extension and verify RMV records `blocked`.
5. Review the dashboard and logs.
6. Set `RMV_DRY_RUN=false` only after observed decisions match policy.

Never use unknown executable payloads as test fixtures. Unit tests cover executable filenames without executing or downloading them.
