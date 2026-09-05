import asyncio
import logging
import secrets
from contextlib import asynccontextmanager, suppress
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from . import __version__
from .automation import AutomationManager, build_automation_providers
from .automation.factory import AUTOMATION_PROVIDER_META
from .clients.factory import CLIENT_PROVIDERS, create_client
from .config import get_settings
from .service import ValidationService
from .store import Store

settings = get_settings()
log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
logging.basicConfig(level=log_level, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
store = Store(settings.data_dir / "rmv.db")
templates = Jinja2Templates(directory="app/templates")
automation_config_error: str | None = None
try:
    automation = AutomationManager(
        build_automation_providers(settings.automation_providers_json),
        store,
    )
except (ValueError, TypeError) as exc:
    automation_config_error = str(exc)
    logging.getLogger("rmv.automation").error(
        "Invalid media automation configuration: %s", exc
    )
    automation = AutomationManager([], store)
admin_security = HTTPBasic(auto_error=False)


def admin_credentials_configured() -> bool:
    return bool(settings.admin_username and settings.admin_password)


def require_admin(
    credentials: Annotated[HTTPBasicCredentials | None, Depends(admin_security)],
):
    if not admin_credentials_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Administrative settings are disabled. Set RMV_ADMIN_USERNAME and "
                "RMV_ADMIN_PASSWORD in .env, then recreate the container."
            ),
        )

    valid = bool(
        credentials
        and secrets.compare_digest(credentials.username, settings.admin_username)
        and secrets.compare_digest(credentials.password, settings.admin_password)
    )
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid administrative credentials.",
            headers={"WWW-Authenticate": 'Basic realm="RogueMediaValidator"'},
        )
    return credentials.username


def provider_meta(provider_id: str) -> dict | None:
    provider_id = provider_id.strip().lower()
    return next((item for item in CLIENT_PROVIDERS if item["id"] == provider_id), None)


def environment_client_config() -> dict | None:
    provider = settings.torrent_client.strip().lower()
    if not provider:
        return None

    meta = provider_meta(provider)
    default_url = str(meta.get("default_url", "")) if meta else ""
    return {
        "provider": provider,
        "url": settings.torrent_url.strip() or default_url,
        "username": settings.torrent_username,
        "password": settings.torrent_password,
    }


def resolved_client_config() -> tuple[dict | None, str]:
    env_config = environment_client_config()
    if env_config:
        return env_config, "environment"

    runtime = store.torrent_client_config()
    if runtime:
        return runtime, "setup"

    return None, "none"


initial_config, _ = resolved_client_config()
initial_client = None
initial_provider = ""
if initial_config:
    try:
        initial_client = create_client(
            initial_config["provider"],
            initial_config["url"],
            initial_config.get("username", ""),
            initial_config.get("password", ""),
        )
        initial_provider = str(initial_config["provider"])
    except (KeyError, ValueError) as exc:
        logging.getLogger("rmv").error("Invalid torrent client configuration: %s", exc)

service = ValidationService(
    settings,
    store,
    initial_client,
    initial_provider,
    automation=automation,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(service.loop())
    try:
        yield
    finally:
        service.stop()
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task
        await service.close()


app = FastAPI(title=settings.app_name, version=__version__, lifespan=lifespan)
app.mount("/static", StaticFiles(directory="app/static"), name="static")


class SetupPayload(BaseModel):
    provider: str
    url: str
    username: str = ""
    password: str = ""


class ManagedScopesPayload(BaseModel):
    scopes: list[str]


def public_client_config() -> dict | None:
    config, source = resolved_client_config()
    if not config:
        return None
    return {
        "provider": config.get("provider"),
        "url": config.get("url"),
        "username": config.get("username", ""),
        "source": source,
    }


def health_payload() -> dict:
    diagnostics = service.snapshot()
    if not service.configured:
        status = "setup_required"
    elif service.last_error:
        status = "degraded"
    elif service.last_success_at:
        status = "healthy"
    else:
        status = "starting"

    connected = bool(
        service.configured
        and service.last_success_at
        and not service.last_error
    )
    return {
        "status": status,
        "version": __version__,
        "dry_run": settings.dry_run,
        "torrent_client_connected": connected,
        "torrent_client": service.client_name or None,
        "torrent_client_name": service.display_name,
        "torrent_client_version": service.last_client_version,
        "supports_delete_data": service.supports_delete_data,
        "last_error": service.last_error,
        "last_success_at": service.last_success_at,
        "diagnostics": diagnostics,
    }


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    if not service.configured:
        return RedirectResponse("/setup", status_code=307)

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "stats": store.stats(),
            "recent": store.recent(30),
            "settings": settings,
            "version": __version__,
            "health": health_payload(),
        },
    )


@app.get("/settings", response_class=HTMLResponse)
async def settings_page(
    request: Request,
    _admin: Annotated[str, Depends(require_admin)],
):
    available = sorted(
        set(service.discovered_scopes) | set(service.managed_scopes)
    )
    return templates.TemplateResponse(
        request=request,
        name="settings.html",
        context={
            "version": __version__,
            "settings": settings,
            "health": health_payload(),
            "available_scopes": available,
            "scope_locked": bool(settings.scopes),
            "admin_username": settings.admin_username,
            "client_config": public_client_config(),
            "automation_providers": AUTOMATION_PROVIDER_META,
            "automation_config_error": automation_config_error,
            "automation_instances": [
                {
                    "provider": provider.provider_id,
                    "name": provider.instance_name,
                    "display_name": provider.display_name,
                }
                for provider in automation.providers
            ],
            "automation_stats": store.automation_stats(),
        },
    )


@app.get("/setup", response_class=HTMLResponse)
async def setup_page(request: Request):
    current = public_client_config()
    locked = service.configured and not settings.setup_unlock
    return templates.TemplateResponse(
        request=request,
        name="setup.html",
        context={
            "version": __version__,
            "providers": CLIENT_PROVIDERS,
            "current": current,
            "configured": service.configured,
            "locked": locked,
        },
    )


async def test_setup_payload(payload: SetupPayload, *, keep_client: bool = False):
    meta = provider_meta(payload.provider)
    if not meta or meta.get("status") != "supported":
        raise HTTPException(status_code=400, detail="Unsupported torrent client.")

    url = payload.url.strip()
    if not url.startswith(("http://", "https://")):
        raise HTTPException(
            status_code=400,
            detail="Torrent client URL must use http:// or https://.",
        )

    client = create_client(
        payload.provider,
        url,
        payload.username,
        payload.password,
    )
    try:
        version = await client.version()
        scopes = await client.scopes()
        result = {
            "provider": payload.provider,
            "name": client.display_name,
            "version": version,
            "scope_name": client.scope_name,
            "scopes": scopes,
            "supports_delete_data": client.supports_delete_data,
        }
        if keep_client:
            return result, client
        await client.close()
        return result, None
    except Exception:
        await client.close()
        raise


@app.post("/api/setup/test")
async def setup_test(payload: SetupPayload):
    try:
        result, _ = await test_setup_payload(payload)
        return {"ok": True, **result}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/setup/save")
async def setup_save(payload: SetupPayload):
    if service.configured and not settings.setup_unlock:
        raise HTTPException(
            status_code=403,
            detail=(
                "Setup is locked after configuration. Set RMV_SETUP_UNLOCK=true "
                "and recreate the container to reconfigure from the web UI."
            ),
        )

    try:
        result, client = await test_setup_payload(payload, keep_client=True)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    assert client is not None
    config = {
        "provider": payload.provider.strip().lower(),
        "url": payload.url.strip(),
        "username": payload.username,
        "password": payload.password,
    }
    store.set_torrent_client_config(config)
    store.clear_bootstrap_scopes(config["provider"])
    await service.reconfigure(client, config["provider"])
    await service.refresh_scopes(force=True)

    return {
        "ok": True,
        **result,
        "managed_scopes": sorted(service.managed_scopes),
        "redirect": "/",
    }


@app.get("/api/setup/providers")
async def setup_providers():
    return CLIENT_PROVIDERS


@app.get("/api/admin/settings")
async def admin_settings(_admin: Annotated[str, Depends(require_admin)]):
    config = public_client_config()
    return {
        "version": __version__,
        "admin_username": settings.admin_username,
        "dry_run": settings.dry_run,
        "torrent_client": service.client_name or None,
        "config_source": config.get("source") if config else "none",
        "scope_name": service.scope_name,
        "scope_source": service.scope_source,
        "scope_locked_by_environment": bool(settings.scopes),
        "environment_scopes": sorted(settings.scopes),
        "managed_scopes": sorted(service.managed_scopes),
        "discovered_scopes": service.discovered_scopes,
        "media_automation": {
            "configured": automation.configured,
            "config_error": automation_config_error,
            "instances": [
                {
                    "provider": provider.provider_id,
                    "name": provider.instance_name,
                    "display_name": provider.display_name,
                }
                for provider in automation.providers
            ],
            "stats": store.automation_stats(),
            "last_results": automation.last_results,
        },
    }


@app.put("/api/admin/scopes")
async def admin_scopes(
    payload: ManagedScopesPayload,
    _admin: Annotated[str, Depends(require_admin)],
):
    if settings.scopes:
        raise HTTPException(
            status_code=409,
            detail=(
                "Managed scopes are controlled by RMV_TORRENT_SCOPES. "
                "Clear that environment value before using UI-managed scopes."
            ),
        )
    if not service.configured:
        raise HTTPException(status_code=409, detail="Torrent client is not configured.")

    requested = {str(value).strip().lower() for value in payload.scopes if str(value).strip()}
    if "*" in requested:
        raise HTTPException(
            status_code=400,
            detail="The wildcard scope can only be configured explicitly through the environment.",
        )

    allowed = {
        str(value).strip().lower()
        for value in [*service.discovered_scopes, *service.managed_scopes]
        if str(value).strip()
    }
    unknown = sorted(requested - allowed)
    if unknown:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown or undiscovered scopes: {', '.join(unknown)}",
        )

    service.set_managed_scopes(sorted(requested))
    return {
        "ok": True,
        "scope_source": service.scope_source,
        "managed_scopes": sorted(service.managed_scopes),
        "fail_closed": not bool(service.managed_scopes),
    }


@app.post("/api/admin/automation/test")
async def automation_test(_admin: Annotated[str, Depends(require_admin)]):
    if automation_config_error:
        raise HTTPException(status_code=400, detail=automation_config_error)
    return {
        "ok": True,
        "configured": automation.configured,
        "results": await automation.test_all(),
    }


@app.get("/api/automation/events")
async def automation_events(
    limit: int = 50,
    _admin: Annotated[str, Depends(require_admin)] = None,
):
    return store.automation_events(max(1, min(limit, 500)))


@app.get("/api/health")
async def health():
    return health_payload()


@app.get("/api/diagnostics")
async def diagnostics():
    snapshot = service.snapshot()
    config = public_client_config()
    return {
        "version": __version__,
        "mode": "dry-run" if settings.dry_run else "enforcing",
        "torrent_client": {
            "provider": service.client_name or None,
            "display_name": service.display_name,
            "configured": service.configured,
            "config_source": config.get("source") if config else "none",
            "url": config.get("url") if config else None,
            "connected": bool(service.last_success_at and not service.last_error),
            "version": service.last_client_version,
            "scope_name": service.scope_name,
            "environment_scopes": sorted(settings.scopes),
            "managed_scopes": sorted(service.managed_scopes),
            "discovered_scopes": service.discovered_scopes,
            "scope_source": service.scope_source,
            "scope_auto_bootstrap": settings.torrent_auto_bootstrap_scopes,
            "scope_bootstrap_complete": snapshot["scope_bootstrap_complete"],
            "scope_fail_closed": not bool(service.managed_scopes),
            "inspect_all_states": settings.torrent_inspect_all_states,
            "action_states": sorted(settings.action_states),
            "supports_delete_data": service.supports_delete_data,
            "policy_fingerprint": settings.policy_fingerprint,
            "quarantine_rejected": settings.quarantine_rejected,
            "quarantined": store.quarantine_count(),
        },
        "media_automation": {
            "configured": automation.configured,
            "config_error": automation_config_error,
            "instances": [
                {
                    "provider": provider.provider_id,
                    "name": provider.instance_name,
                    "display_name": provider.display_name,
                }
                for provider in automation.providers
            ],
            "stats": store.automation_stats(),
            "last_results": automation.last_results,
        },
        "service": snapshot,
        "storage": store.stats(),
    }


@app.get("/api/quarantine")
async def quarantine(limit: int = 50):
    return store.quarantine_recent(max(1, min(limit, 500)))


@app.get("/api/validations")
async def validations(limit: int = 50):
    return store.recent(max(1, min(limit, 500)))


@app.get("/api/stats")
async def stats():
    return store.stats()
