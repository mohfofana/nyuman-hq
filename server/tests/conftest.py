import os

os.environ["HQ_DATABASE_URL"] = "postgresql+asyncpg://localhost/nyuman_hq_test"

import pytest  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402

from app.db import Base, SessionLocal, create_schema, engine  # noqa: E402
from app.domain.seed import seed  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
async def fresh_db():
    from app.domain import models  # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await create_schema()
    async with SessionLocal() as s:
        await seed(s)
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
