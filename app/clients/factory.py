from .base import TorrentClient
from .qbittorrent import QBittorrentClient
from .transmission import TransmissionClient

CLIENT_PROVIDERS = [
    {
        "id": "qbittorrent",
        "name": "qBittorrent",
        "status": "supported",
        "default_url": "http://qbittorrent:8080",
        "scope_name": "Categories",
        "description": "Native Web API integration with category discovery.",
    },
    {
        "id": "transmission",
        "name": "Transmission",
        "status": "supported",
        "default_url": "http://transmission:9091/transmission/rpc",
        "scope_name": "Labels",
        "description": "Transmission 3.x/4.x RPC integration using torrent labels.",
    },
    {
        "id": "deluge",
        "name": "Deluge",
        "status": "planned",
        "default_url": "http://deluge:8112",
        "scope_name": "Labels",
        "description": "Adapter planned for a following 0.4.x release.",
    },
    {
        "id": "rtorrent",
        "name": "rTorrent / ruTorrent",
        "status": "planned",
        "default_url": "",
        "scope_name": "Labels",
        "description": "Adapter planned after the core setup workflow is proven.",
    },
]


def create_client(
    provider: str,
    base_url: str,
    username: str = "",
    password: str = "",
) -> TorrentClient:
    provider = provider.strip().lower()
    if provider == "qbittorrent":
        return QBittorrentClient(base_url, username, password)
    if provider == "transmission":
        return TransmissionClient(base_url, username, password)
    raise ValueError(f"Unsupported torrent client: {provider}")
