from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import StaticPool

from adapters.common.ports.out.cached_stats_gateway import reset_cache
from adapters.common.ports.out.nyuman_db_stats_gateway import NyumanDbStatsGateway

# Les trois tables de nyuman-api, réduites aux colonnes que le compte de lecture a le droit de voir.
SCHEMA = [
    'CREATE TABLE "user" (id INTEGER PRIMARY KEY, is_active BOOLEAN, is_deleted BOOLEAN)',
    "CREATE TABLE reservation (id INTEGER PRIMARY KEY, provider_id INTEGER, is_deleted BOOLEAN)",
    """CREATE TABLE acompte_escrow (
        id INTEGER PRIMARY KEY, reservation_id INTEGER, acompte FLOAT, frais_nyuman FLOAT,
        promo_compensation FLOAT, status VARCHAR(50), created_at TIMESTAMP, released_at TIMESTAMP,
        is_deleted BOOLEAN)""",
]


@pytest.fixture(autouse=True)
def _clean_cache():
    reset_cache()
    yield
    reset_cache()


@pytest.fixture
async def engine():
    engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    days = lambda n: (now - timedelta(days=n)).isoformat(sep=" ")  # noqa: E731
    async with engine.begin() as conn:
        for statement in SCHEMA:
            await conn.execute(text(statement))
        # 3 comptes activés, 1 non activé (OTP jamais validé), 1 supprimé.
        await conn.execute(text(
            'INSERT INTO "user" VALUES (1,1,0),(2,1,0),(3,1,0),(4,0,0),(5,1,1)'
        ))
        # Réservations des pros 10, 11 et 12 ; la 4 est supprimée.
        await conn.execute(text("INSERT INTO reservation VALUES (1,10,0),(2,10,0),(3,11,0),(4,12,1),(5,13,0)"))
        rows = [
            # id, réservation, acompte, frais Nyuman, promo, statut, créé il y a, reversé il y a
            (1, 1, 3600, 198, 0, "RELEASED", days(2), days(1)),
            (2, 2, 1500, 100, 50, "HELD", days(3), None),
            (3, 3, 2400, 132, 0, "REFUNDED", days(4), None),
            (4, 4, 9000, 495, 0, "HELD", days(1), None),  # réservation supprimée
            (5, 5, 6000, 330, 0, "RELEASED", days(20), days(15)),  # hors 7 jours, dans 30 jours
        ]
        for r in rows:
            await conn.execute(
                text("INSERT INTO acompte_escrow VALUES (:i,:r,:a,:f,:p,:s,:c,:rel,0)"),
                dict(zip(["i", "r", "a", "f", "p", "s", "c", "rel"], r)),
            )
    yield engine
    await engine.dispose()


async def test_calcule_les_totaux_sans_donnees_personnelles(engine):
    snapshot = await NyumanDbStatsGateway(engine).snapshot()

    assert snapshot.available is True
    values = {k.key: k.value for k in snapshot.values}
    assert values["utilisateurs_inscrits"] == 3
    # Pros 10, 11 et 13 : la réservation du pro 12 est supprimée.
    assert values["pros_actifs"] == 3
    # Acomptes 1 et 2 de moins de 7 jours ; le 3 est remboursé, le 4 tient à une réservation supprimée.
    assert values["reservations_7j"] == 2
    assert values["acomptes_7j_fcfa"] == 3600 + 1500
    # Seul l'acompte 1 a été reversé ces 7 derniers jours.
    assert values["revenu_nyuman_7j_fcfa"] == 198


async def test_base_injoignable_sans_casser_le_salon():
    engine = create_async_engine("sqlite+aiosqlite:///Z:/dossier/inexistant/base.db")
    snapshot = await NyumanDbStatsGateway(engine).snapshot()
    assert snapshot.available is False
    await engine.dispose()
