# Security Policy

RogueMediaValidator is a safety boundary for automated media downloads and should be deployed with least privilege.

- Keep RMV and the selected torrent client on a trusted/private container network.
- Do not expose torrent-client credentials publicly.
- Use a dedicated restricted torrent-client account when the client supports that model.
- Start with `RMV_DRY_RUN=true` and review decisions before enforcement.
- The RMV container runs non-root, drops Linux capabilities and uses `no-new-privileges`.
- Do not mount Docker or Podman sockets into RMV.
- RMV intentionally fails closed for unknown payload file extensions.
- Setup credentials saved through the browser remain in RMV's private data volume and are never returned through diagnostics.
- Setup writes lock automatically after provider configuration unless `RMV_SETUP_UNLOCK=true`.
- Keep `RMV_SETUP_UNLOCK=false` during normal operation.
- Do not expose an unconfigured or explicitly unlocked Installation page directly to the public Internet.
- Use HTTPS and an authenticated reverse proxy before exposing RMV beyond a trusted network.

The first-run setup endpoint can initiate HTTP requests to the torrent-client URL supplied by the administrator. Treat setup access as administrative access and keep it restricted.

Report security issues privately to the repository owner rather than posting exploit details in a public issue.
