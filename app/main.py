import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import __version__
from .config import get_settings
from .qbittorrent import QBittorrentClient
from .service import ValidationService
from .store import Store

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
settings = get_settings()
store = Store(settings.data_dir / "rmv.db")
qb = QBittorrentClient(settings.qb_url, settings.qb_username, settings.qb_password)
service = ValidationService(settings, store, qb)
templates = Jinja2Templates(directory="app/templates")


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(service.loop())
    yield
    service.stop()
    task.cancel()
    await qb.close()


app = FastAPI(title=settings.app_name, version=__version__, lifespan=lifespan)
app.mount("/static", StaticFiles(directory="app/static"), name="static")


def health_payload() -> dict:
    diagnostics = service.snapshot()
    if service.last_error:
        status = "degraded"
    elif service.last_success_at:
        status = "healthy"
    else:
        status = "starting"
    return {
        "status": status,
        "version": __version__,
        "dry_run": settings.dry_run,
        "qbittorrent_connected": bool(service.last_success_at and not service.last_error),
        "qbittorrent_version": service.last_qb_version,
        "last_error": service.last_error,
        "last_success_at": service.last_success_at,
        "diagnostics": diagnostics,
    }


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
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


@app.get("/api/health")
async def health():
    return health_payload()


@app.get("/api/diagnostics")
async def diagnostics():
    return {
        "version": __version__,
        "mode": "dry-run" if settings.dry_run else "enforcing",
        "qbittorrent": {
            "url": settings.qb_url,
            "connected": bool(service.last_success_at and not service.last_error),
            "version": service.last_qb_version,
            "categories": sorted(settings.categories),
            "inspect_all_states": settings.qb_inspect_all_states,
            "action_states": sorted(settings.action_states),
        },
        "service": service.snapshot(),
        "storage": store.stats(),
    }


@app.get("/api/validations")
async def validations(limit: int = 50):
    return store.recent(max(1, min(limit, 500)))


@app.get("/api/stats")
async def stats():
    return store.stats()
