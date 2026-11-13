import os

os.environ["HQ_DATABASE_URL"] = "postgresql+asyncpg://localhost/nyuman_hq_test"
os.environ["HQ_UPLOAD_DIR"] = "/tmp/nyuman_hq_test_uploads"

import pytest  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402

from app.db import Base, SessionLocal, create_schema, engine  # noqa: E402
from app.domain.seed import seed, seed_channels, seed_org  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
async def fresh_db():
    from app.domain import models  # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await create_schema()
    async with SessionLocal() as s:
        await seed(s)
        await seed_channels(s)
        await seed_org(s)
    yield


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.fixture
async def mohamed(client):
    r = await client.post("/api/auth/dev-login", json={"member_id": "mohamed"})
    assert r.status_code == 200
    return client


async def login_as(member_id):
    c = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
    r = await c.post("/api/auth/dev-login", json={"member_id": member_id})
    assert r.status_code == 200
    return c


@pytest.fixture
async def kevin():
    c = await login_as("kevin")
    yield c
    await c.aclose()


@pytest.fixture
async def sullyvan():
    c = await login_as("sullyvan")
    yield c
    await c.aclose()
