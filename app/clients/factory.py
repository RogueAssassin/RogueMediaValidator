from .aria2 import Aria2Client
from .base import TorrentClient
from .deluge import DelugeClient
from .qbittorrent import QBittorrentClient
from .rtorrent import RTorrentClient
from .transmission import TransmissionClient

CLIENT_PROVIDERS = [
    {
        "id": "qbittorrent",
        "name": "qBittorrent",
        "status": "supported",
        "default_url": "http://qbittorrent:8080",
        "scope_name": "Categories",
        "description": "Native Web API integration with category discovery.",
        "username_label": "Username",
        "password_label": "Password",
        "credential_hint": "Use the qBittorrent Web UI credentials.",
        "supports_delete_data": True,
    },
    {
        "id": "transmission",
        "name": "Transmission",
        "status": "supported",
        "default_url": "http://transmission:9091/transmission/rpc",
        "scope_name": "Labels",
        "description": "Transmission RPC integration using torrent labels.",
        "username_label": "Username",
        "password_label": "Password",
        "credential_hint": "Optional HTTP Basic authentication.",
        "supports_delete_data": True,
    },
    {
        "id": "deluge",
        "name": "Deluge",
        "status": "supported",
        "default_url": "http://deluge:8112/json",
        "scope_name": "Labels / download paths",
        "description": "Deluge Web JSON-RPC with label and download-path scope discovery.",
        "username_label": "Username",
        "password_label": "Web UI password",
        "credential_hint": "Deluge Web normally authenticates with the Web UI password; username is optional.",
        "supports_delete_data": True,
    },
    {
        "id": "rtorrent",
        "name": "rTorrent / ruTorrent",
        "status": "supported",
        "default_url": "http://rutorrent/RPC2",
        "scope_name": "Labels / download paths",
        "description": "rTorrent XML-RPC using custom1 labels with directory fallback.",
        "username_label": "HTTP username",
        "password_label": "HTTP password",
        "credential_hint": "Use reverse-proxy Basic Auth credentials when your RPC endpoint requires them.",
        "supports_delete_data": False,
    },
    {
        "id": "aria2",
        "name": "aria2",
        "status": "supported",
        "default_url": "http://aria2:6800/jsonrpc",
        "scope_name": "Download paths",
        "description": "aria2 JSON-RPC BitTorrent integration using download directories as scopes.",
        "username_label": "Unused",
        "password_label": "RPC secret",
        "credential_hint": "Put the aria2 RPC secret in the password field. Username is ignored.",
        "supports_delete_data": False,
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
    if provider == "deluge":
        return DelugeClient(base_url, username, password)
    if provider == "rtorrent":
        return RTorrentClient(base_url, username, password)
    if provider == "aria2":
        return Aria2Client(base_url, username, password)
    raise ValueError(f"Unsupported torrent client: {provider}")
