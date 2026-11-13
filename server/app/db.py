from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    pass


engine = create_async_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_session():
    async with SessionLocal() as session:
        yield session


async def create_schema(eng=engine) -> None:
    from app.domain import models  # noqa: F401  (enregistre les tables)

    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Colonnes ajoutées après coup (pas d'Alembic : on reste simple et sans risque).
        for stmt in LATER_COLUMNS:
            await conn.exec_driver_sql(stmt)


LATER_COLUMNS = [
    "ALTER TABLE members ADD COLUMN IF NOT EXISTS work_days VARCHAR(20) NOT NULL DEFAULT '1,2,3,4,5'",
    "ALTER TABLE members ADD COLUMN IF NOT EXISTS ask_hour INTEGER DEFAULT 19",
    "ALTER TABLE projects ADD COLUMN IF NOT EXISTS hours_budget INTEGER",
    "ALTER TABLE members ADD COLUMN IF NOT EXISTS email VARCHAR(160) NOT NULL DEFAULT ''",
    "CREATE UNIQUE INDEX IF NOT EXISTS members_email_uq ON members (lower(email)) WHERE email <> ''",
]
