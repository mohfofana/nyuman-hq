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
