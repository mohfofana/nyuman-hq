import logging
from datetime import datetime, timezone
from typing import Optional

import httpx

from adapters.common.ports.out.cached_stats_gateway import CachedStatsGateway, reset_cache  # noqa: F401
from domain.value_objects.kpi import KPI_KEYS, KpiSnapshot

logger = logging.getLogger("hq")

NON_BRANCHEE = (
    "Les chiffres de l’app Nyuman ne sont pas encore branchés. "
    "Il faut renseigner NYUMAN_DB_LECTURE_URL (lecture seule de la base) sur le serveur de HQ."
)


class NyumanStatsGateway(CachedStatsGateway):
    """Lit les totaux par la route GET /statistiques/hq de nyuman-api (si elle est un jour déployée)."""

    def __init__(
        self,
        base_url: Optional[str],
        api_key: Optional[str],
        cache_seconds: int = 60,
        transport: Optional[httpx.AsyncBaseTransport] = None,
    ):
        super().__init__(cache_seconds)
        self._base_url = base_url.rstrip("/") if base_url else None
        self._api_key = api_key
        self._transport = transport

    async def snapshot(self) -> KpiSnapshot:
        if not self._base_url or not self._api_key:
            return KpiSnapshot.unavailable(NON_BRANCHEE)
        return await super().snapshot()

    async def _fetch(self) -> Optional[KpiSnapshot]:
        try:
            async with httpx.AsyncClient(timeout=5.0, transport=self._transport) as client:
                response = await client.get(
                    f"{self._base_url}/statistiques/hq", headers={"X-Stats-Key": self._api_key}
                )
            response.raise_for_status()
            data = response.json()
            totals = {key: float(data[key]) for key in KPI_KEYS if key in data}
        except (httpx.HTTPError, ValueError, TypeError, KeyError) as exc:
            logger.warning("Statistiques Nyuman indisponibles : %s", exc)
            return None
        return KpiSnapshot.from_totals(totals, datetime.now(timezone.utc))
