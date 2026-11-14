import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api import appstats, auth, chat, files, live, meetings, members, org, projects, space, timesheet
from app.config import settings
from app.db import SessionLocal, create_schema
from app.domain.seed import seed, seed_channels, seed_org


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await create_schema()
    from app.api.auth import ensure_session_secret
    await ensure_session_secret()
    async with SessionLocal() as session:
        await seed(session)
        await seed_channels(session)
        await seed_org(session)
        from sqlalchemy import select
        from app.domain.models import Member
        from app.realtime import hub
        hub.agents = set((await session.scalars(select(Member.id).where(Member.kind == "agent"))).all())
    tasks = []
    if settings.meetings_scheduler:
        tasks.append(asyncio.create_task(meetings.scheduler()))
    if settings.agent_poll:
        from app.wake import poll_loop
        tasks.append(asyncio.create_task(poll_loop()))
    yield
    for t in tasks:
        t.cancel()


app = FastAPI(title="Nyuman HQ", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth.router)
app.include_router(members.router)
app.include_router(chat.router)
app.include_router(timesheet.router)
app.include_router(space.router)
app.include_router(appstats.router)

# En ligne, le même serveur sert le site compilé (web/dist) : une seule adresse, pas de CORS.
_web = Path(settings.web_dir) if settings.web_dir else None
if _web and (_web / "index.html").exists():
    app.mount("/assets", StaticFiles(directory=_web / "assets"), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def site(full_path: str):
        """Un fichier s'il existe, sinon la page d'accueil (les adresses sont gérées côté navigateur)."""
        candidate = (_web / full_path).resolve()
        if full_path and _web.resolve() in candidate.parents and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(_web / "index.html")
app.include_router(files.router)
app.include_router(live.router)
app.include_router(meetings.router)
app.include_router(org.router)
app.include_router(projects.router)


@app.get("/api/health")
async def health():
    return {"ok": True}
