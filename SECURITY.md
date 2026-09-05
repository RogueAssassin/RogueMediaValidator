# Security Policy

RogueMediaValidator is a safety boundary for automated torrent downloads and should be deployed with least privilege.

- Keep RMV and the selected torrent client on a trusted/private container network.
- Start with `RMV_DRY_RUN=true`.
- Do not mount Docker or Podman sockets.
- Keep `RMV_SETUP_UNLOCK=false` during normal operation.
- Setup credentials are stored in the private RMV data volume and are not returned by diagnostics.
- Set a strong unique `RMV_ADMIN_PASSWORD`; there is no default admin password.
- Treat torrent-client credentials, automation API keys and webhook tokens as secrets.
- Do not expose an unlocked Installation page directly to the public Internet.
- Use HTTPS and authentication before exposing RMV outside a trusted network.
- RMV fails closed for unknown payload file extensions.

## Provider-specific limits

qBittorrent, Transmission and Deluge can remove local payload data through their supported APIs.

rTorrent/ruTorrent and aria2 cannot safely guarantee payload filesystem deletion through the RPC methods RMV uses. RMV exposes this limitation and records a limited enforcement result instead of reporting full success.

For those providers, the preferred deployment is a true pre-download gate where torrents arrive stopped/paused before payload data is transferred.

## Setup URL security

The Installation page can initiate HTTP requests to an administrator-supplied torrent-client URL. Treat setup access as administrative access.

Report security issues privately to the repository owner rather than posting exploit details publicly.
