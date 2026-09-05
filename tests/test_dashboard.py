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
        torrent_inspect_all_states=True,
        action_states=frozenset({"pauseddl", "stoppeddl", "downloading"}),
    )
    health = {
        "status": "healthy",
        "torrent_client_connected": True,
        "torrent_client_name": "Transmission",
        "torrent_client_version": "4.1.1",
        "supports_delete_data": True,
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
        "limited_actions": 0,
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
        version="0.5.0",
    )

    assert "RogueMediaValidator" in rendered
    assert "Transmission protection at a glance" in rendered
    assert "Managed labels" in rendered
    assert "movies" in rendered
    assert "manual" in rendered
    assert "Unsafe release.exe" in rendered
    assert "Settings" in rendered
    assert "Installation" in rendered
    assert "Diagnostics" in rendered
    assert "Delete payload data" in rendered


def test_setup_template_lists_all_supported_providers():
    template = template_env().get_template("setup.html")
    providers = [
        {
            "id": "qbittorrent",
            "name": "qBittorrent",
            "status": "supported",
            "default_url": "http://qbittorrent:8080",
            "scope_name": "Categories",
            "description": "qBittorrent support",
            "username_label": "Username",
            "password_label": "Password",
            "credential_hint": "Web UI credentials",
            "supports_delete_data": True,
        },
        {
            "id": "transmission",
            "name": "Transmission",
            "status": "supported",
            "default_url": "http://transmission:9091/transmission/rpc",
            "scope_name": "Labels",
            "description": "Transmission support",
            "username_label": "Username",
            "password_label": "Password",
            "credential_hint": "Optional Basic Auth",
            "supports_delete_data": True,
        },
        {
            "id": "deluge",
            "name": "Deluge",
            "status": "supported",
            "default_url": "http://deluge:8112/json",
            "scope_name": "Labels / download paths",
            "description": "Deluge support",
            "username_label": "Username",
            "password_label": "Web UI password",
            "credential_hint": "Deluge Web password",
            "supports_delete_data": True,
        },
        {
            "id": "rtorrent",
            "name": "rTorrent / ruTorrent",
            "status": "supported",
            "default_url": "http://rutorrent/RPC2",
            "scope_name": "Labels / download paths",
            "description": "rTorrent support",
            "username_label": "HTTP username",
            "password_label": "HTTP password",
            "credential_hint": "Basic Auth when required",
            "supports_delete_data": False,
        },
        {
            "id": "aria2",
            "name": "aria2",
            "status": "supported",
            "default_url": "http://aria2:6800/jsonrpc",
            "scope_name": "Download paths",
            "description": "aria2 support",
            "username_label": "Unused",
            "password_label": "RPC secret",
            "credential_hint": "aria2 RPC secret",
            "supports_delete_data": False,
        },
    ]

    rendered = template.render(
        version="0.5.0",
        providers=providers,
        current=None,
        configured=False,
        locked=False,
    )

    for provider in providers:
        assert provider["name"] in rendered
    assert "torrent entry only" in rendered
    assert "Save & finish setup" in rendered


def test_settings_template_explains_configuration_ownership():
    template = template_env().get_template("settings.html")
    settings = SimpleNamespace(dry_run=True)
    health = {
        "torrent_client_name": "qBittorrent",
        "diagnostics": {
            "scope_name": "categories",
            "scope_source": "ui",
            "managed_scopes": ["movies"],
        },
    }

    rendered = template.render(
        version="0.6.0",
        settings=settings,
        health=health,
        available_scopes=["movies", "tv"],
        scope_locked=False,
        admin_username="operator",
        client_config={"source": "setup"},
    )

    assert "0.6.0 operator control" in rendered
    assert "Save managed scopes" in rendered
    assert "movies" in rendered
    assert "Discovered, not managed" in rendered
    assert "Fail closed" in rendered
    assert "Environment priority" in rendered
