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
    # L'adresse unique d'hier devient une liste (chacun peut avoir sa pro et sa perso).
    """DO $$ BEGIN
         IF EXISTS (SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'members' AND column_name = 'email') THEN
           INSERT INTO member_emails (email, member_id)
             SELECT lower(email), id FROM members WHERE email <> ''
             ON CONFLICT DO NOTHING;
           ALTER TABLE members DROP COLUMN email;
         END IF;
       END $$;""",
]
