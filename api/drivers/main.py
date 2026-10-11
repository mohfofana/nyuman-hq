import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from alembic import command
from alembic.config import Config
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from adapters.common.providers import get_capture_storage, get_testflight_gateway
from adapters.core.retour.retour_app_config import RetourAppConfig, TestflightState
from core.config import settings
from core.database import SessionLocal
from core.exception_handler import setup_exception_handlers
from core.origin_middleware import OriginCheckMiddleware
from core.security_headers import SecurityHeadersMiddleware
import core.realtime.evenement_broadcast  # noqa: F401  (diffusion du fil en direct après chaque commit)
from drivers.seed import seed
from drivers.utils import discover_and_include_routers

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("hq")

API_DIR = Path(__file__).resolve().parent.parent


def run_migrations() -> None:
    config = Config(str(API_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(API_DIR / "migrations"))
    config.attributes["configure_logger"] = False  # garder les journaux d'uvicorn tels quels
    command.upgrade(config, "head")


async def _testflight_loop() -> None:
    """Import TestFlight à intervalle fixe (pas en boucle serrée), seulement si la clé est renseignée."""
    while True:
        await asyncio.sleep(settings.TESTFLIGHT_SYNC_MINUTES * 60)
        try:
            async with SessionLocal() as session:
                config = RetourAppConfig(session, get_capture_storage(), get_testflight_gateway())
                nouveaux = await config.sync_retours_use_case()()
            TestflightState.derniere_synchro = datetime.now(timezone.utc)
            TestflightState.derniere_erreur = None
            if nouveaux:
                logger.info("TestFlight : %s nouveau(x) retour(s)", nouveaux)
        except Exception as exc:
            TestflightState.derniere_erreur = str(exc)[:200]
            logger.warning("Import TestFlight impossible : %s", exc)


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Les migrations Alembic tournent dans un fil à part : elles ouvrent leur propre boucle asynchrone.
    await asyncio.to_thread(run_migrations)
    async with SessionLocal() as session:
        await seed(session, settings.heads_initiaux)
    if settings.dev_login_enabled:
        logger.warning("Connexion de développement activée (HQ_DEV_LOGIN). Jamais en production.")
    background = asyncio.create_task(_testflight_loop()) if get_testflight_gateway().configured else None
    yield
    if background:
        background.cancel()


def create_app(with_lifespan: bool = True) -> FastAPI:
    production = settings.ENVIRONMENT == "production"
    app = FastAPI(
        title="Nyuman HQ",
        lifespan=lifespan if with_lifespan else None,
        docs_url=None if production else "/api/docs",
        openapi_url=None if production else "/api/openapi.json",
        redoc_url=None,
    )
    app.add_middleware(OriginCheckMiddleware, allowed_origins=settings.origines)
    app.add_middleware(SecurityHeadersMiddleware, production=production)
    setup_exception_handlers(app)

    @app.get("/api/sante", tags=["Santé"])
    async def sante() -> dict:
        return {"ok": True}

    discover_and_include_routers(app)
    _serve_web(app)
    return app


def _serve_web(app: FastAPI) -> None:
    """En production, le même serveur sert l'interface React construite (web/dist) : une seule adresse."""
    web_dir = (API_DIR / settings.HQ_WEB_DIR).resolve()
    index = web_dir / "index.html"
    if not index.is_file():
        return
    if (web_dir / "assets").is_dir():
        app.mount("/assets", StaticFiles(directory=web_dir / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    async def spa(path: str) -> FileResponse:
        if path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Introuvable.")
        candidate = (web_dir / path).resolve()
        if path and candidate.is_file() and candidate.is_relative_to(web_dir):
            return FileResponse(candidate)
        return FileResponse(index)


app = create_app()
