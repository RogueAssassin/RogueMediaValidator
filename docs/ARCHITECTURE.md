# Architecture

Radarr/Sonarr add torrents to qBittorrent in a paused state. RMV polls qBittorrent, filters to configured categories, obtains the torrent file list and validates the entire payload. Approved torrents may be resumed; rejected torrents may be removed and their data deleted. Every completed decision is persisted in SQLite and surfaced through the dashboard/API.

The first testing release deliberately keeps RMV independent of Radarr/Sonarr APIs. Direct failed-download feedback is planned after payload enforcement is validated safely in production-like testing.
