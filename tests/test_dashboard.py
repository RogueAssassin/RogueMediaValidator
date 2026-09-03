from types import SimpleNamespace

from jinja2 import Environment, FileSystemLoader, select_autoescape


def template_env():
    return Environment(
        loader=FileSystemLoader("app/templates"),
        autoescape=select_autoescape(["html", "xml"]),
    )


def test_dashboard_template_renders_with_generic_client_context():
    template = template_env().get_template("index.html")

    settings = SimpleNamespace(
        dry_run=True,
        policy_fingerprint="abc123",
        poll_seconds=2,
        inspect_all_states=True,
        action_states=frozenset({"pauseddl", "stoppeddl", "downloading"}),
    )
    health = {
        "status": "healthy",
        "torrent_client_connected": True,
        "torrent_client_name": "Transmission",
        "torrent_client_version": "4.1.1",
        "diagnostics": {
            "client_display_name": "Transmission",
            "torrents_seen": 2,
            "in_scope_torrents": 1,
            "actionable_torrents": 1,
            "scope_name": "labels",
            "managed_scopes": ["movies", "tv"],
            "discovered_scopes": ["manual", "movies", "tv"],
            "scope_source": "auto_bootstrap",
            "scope_bootstrap_complete": True,
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
        version="0.4.0",
    )

    assert "RogueMediaValidator" in rendered
    assert "Transmission protection at a glance" in rendered
    assert "Managed labels" in rendered
    assert "movies" in rendered
    assert "manual" in rendered
    assert "Unsafe release.exe" in rendered
    assert "Installation" in rendered
    assert "Diagnostics" in rendered


def test_setup_template_lists_supported_and_planned_providers():
    template = template_env().get_template("setup.html")
    providers = [
        {
            "id": "qbittorrent",
            "name": "qBittorrent",
            "status": "supported",
            "default_url": "http://qbittorrent:8080",
            "scope_name": "Categories",
            "description": "qBittorrent support",
        },
        {
            "id": "transmission",
            "name": "Transmission",
            "status": "supported",
            "default_url": "http://transmission:9091/transmission/rpc",
            "scope_name": "Labels",
            "description": "Transmission support",
        },
        {
            "id": "deluge",
            "name": "Deluge",
            "status": "planned",
            "default_url": "http://deluge:8112",
            "scope_name": "Labels",
            "description": "Coming later",
        },
    ]

    rendered = template.render(
        version="0.4.0",
        providers=providers,
        current=None,
        configured=False,
        locked=False,
    )

    assert "Connect your torrent client" in rendered
    assert "qBittorrent" in rendered
    assert "Transmission" in rendered
    assert "Deluge" in rendered
    assert "Save &amp; finish setup" not in rendered
    assert "Save & finish setup" in rendered
