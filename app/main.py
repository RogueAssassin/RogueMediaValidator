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


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"stats": store.stats(), "recent": store.recent(30), "settings": settings, "version": __version__},
    )


@app.get("/api/health")
async def health():
    return {
        "status": "healthy" if not service.last_error else "degraded",
        "version": __version__,
        "dry_run": settings.dry_run,
        "last_error": service.last_error,
    }


@app.get("/api/validations")
async def validations(limit: int = 50):
    return store.recent(max(1, min(limit, 500)))


@app.get("/api/stats")
async def stats():
    return store.stats()
