import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from adapters.common.ports.out.cached_stats_gateway import CachedStatsGateway
from domain.value_objects.kpi import KPI_KEYS, KpiSnapshot

logger = logging.getLogger("hq")

# Lecture directe de la base de nyuman-api, sans toucher à son code.
# Le compte de lecture n'a le droit de voir que les colonnes ci-dessous (voir docs/lecture-base-nyuman.md) :
# aucun nom, email ni téléphone ne peut sortir de la base, seulement ces totaux.
#
# Définitions (identiques à celles du README) :
# - un acompte_escrow n'existe que si l'acompte d'une réservation a été payé (webhook Paystack) ;
# - Nyuman garde frais_nyuman quand l'acompte est reversé au pro, et paie promo_compensation.
#
# Les colonnes sont nommées une à une (jamais de *) : le compte de lecture n'a pas le droit de voir les autres.
STATS_SQL = text(
    """
    WITH paye AS (
      SELECT r.provider_id, e.acompte, e.frais_nyuman, e.promo_compensation, e.status, e.created_at, e.released_at
      FROM acompte_escrow e
      JOIN reservation r ON r.id = e.reservation_id
      WHERE e.is_deleted IS FALSE AND r.is_deleted IS FALSE
    )
    SELECT
      (SELECT count(*) FROM "user" u
         WHERE u.is_active IS TRUE AND u.is_deleted IS FALSE) AS utilisateurs_inscrits,
      (SELECT count(DISTINCT provider_id) FROM paye
         WHERE created_at >= :depuis_30j) AS pros_actifs,
      (SELECT count(*) FROM paye
         WHERE status <> 'REFUNDED' AND created_at >= :depuis_7j) AS reservations_7j,
      (SELECT coalesce(sum(acompte), 0) FROM paye
         WHERE status <> 'REFUNDED' AND created_at >= :depuis_7j) AS acomptes_7j_fcfa,
      (SELECT coalesce(sum(coalesce(frais_nyuman, 0) - coalesce(promo_compensation, 0)), 0) FROM paye
         WHERE status = 'RELEASED' AND released_at >= :depuis_7j) AS revenu_nyuman_7j_fcfa
    """
)


class NyumanDbStatsGateway(CachedStatsGateway):
    def __init__(self, engine: AsyncEngine, cache_seconds: int = 60):
        super().__init__(cache_seconds)
        self._engine = engine

    async def _fetch(self) -> Optional[KpiSnapshot]:
        # nyuman-api enregistre ses dates sans fuseau, en UTC (serveur et Abidjan sont à UTC+0).
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        params = {"depuis_7j": now - timedelta(days=7), "depuis_30j": now - timedelta(days=30)}
        try:
            async with self._engine.connect() as conn:
                if conn.dialect.name == "postgresql":
                    await conn.execute(text("SET TRANSACTION READ ONLY"))
                row = (await conn.execute(STATS_SQL, params)).mappings().one()
        except Exception as exc:  # base injoignable, droits manquants… : le salon affiche un message, rien ne casse
            logger.warning("Lecture de la base Nyuman impossible : %s", exc)
            return None
        totals = {key: float(row[key] or 0) for key in KPI_KEYS}
        return KpiSnapshot.from_totals(totals, datetime.now(timezone.utc))
