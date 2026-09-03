from types import SimpleNamespace

from jinja2 import Environment, FileSystemLoader, select_autoescape


def test_dashboard_template_renders_with_runtime_context():
    env = Environment(
        loader=FileSystemLoader("app/templates"),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template("index.html")

    settings = SimpleNamespace(
        dry_run=True,
        policy_fingerprint="abc123",
        poll_seconds=2,
        qb_inspect_all_states=True,
        qb_action_states="pausedDL,stoppedDL,downloading",
    )
    health = {
        "status": "healthy",
        "qbittorrent_connected": True,
        "qbittorrent_version": "v5.2.3",
        "diagnostics": {
            "torrents_seen": 1,
            "in_scope_torrents": 1,
            "actionable_torrents": 0,
            "managed_categories": ["radarr", "tv"],
            "discovered_categories": ["manual", "radarr", "tv"],
            "category_source": "auto_bootstrap",
            "category_bootstrap_complete": True,
        },
    }
    stats = {
        "total": 1,
        "approved": 0,
        "blocked": 1,
        "enforced": 0,
        "action_failures": 0,
    }
    recent = [
        {
            "status": "blocked",
            "torrent_name": "Unsafe release.exe",
            "category": "tv",
            "video_files": 0,
            "action": "none",
            "action_status": "audit",
            "reason": "Blocked file type detected",
        }
    ]

    rendered = template.render(
        settings=settings,
        health=health,
        stats=stats,
        recent=recent,
        version="0.3.1",
    )

    assert "RogueMediaValidator" in rendered
    assert "Managed categories" in rendered
    assert "radarr" in rendered
    assert "tv" in rendered
    assert "manual" in rendered
    assert "Unsafe release.exe" in rendered
    assert "Diagnostics" in rendered
