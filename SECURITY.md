# Security Policy

RogueMediaValidator is a security boundary for automated media downloads, but should be deployed with least privilege.

- Keep RMV and qBittorrent on a private container network.
- Do not expose qBittorrent credentials publicly.
- Use a dedicated qBittorrent account when practical.
- Start with `RMV_DRY_RUN=true` and review decisions before enforcement.
- The container runs non-root, drops Linux capabilities and uses `no-new-privileges` in compose.
- RMV intentionally fails closed for unknown payload file extensions.

Report security issues privately to the repository owner rather than posting exploit details in a public issue.
