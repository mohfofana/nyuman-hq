import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, chat, files, live, meetings, members, org
from app.config import settings
from app.db import SessionLocal, create_schema
from app.domain.seed import seed, seed_channels, seed_org


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await create_schema()
    async with SessionLocal() as session:
        await seed(session)
        await seed_channels(session)
        await seed_org(session)
    task = asyncio.create_task(meetings.scheduler())
    yield
    task.cancel()


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
app.include_router(files.router)
app.include_router(live.router)
app.include_router(meetings.router)
app.include_router(org.router)


@app.get("/api/health")
async def health():
    return {"ok": True}
