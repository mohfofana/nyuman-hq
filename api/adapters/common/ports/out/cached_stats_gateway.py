import time
from abc import abstractmethod
from typing import Optional

from domain.value_objects.kpi import KpiSnapshot
from use_cases.common.ports.out.stats_gateway import StatsGateway

INJOIGNABLE = "Les chiffres de l’app Nyuman ne répondent pas pour l’instant. Nouvel essai dans une minute."


class _Cache:
    """Une seule lecture par minute, quel que soit le nombre d'écrans ouverts."""

    snapshot: Optional[KpiSnapshot] = None
    fetched_at: float = 0.0


def reset_cache() -> None:
    _Cache.snapshot = None
    _Cache.fetched_at = 0.0


class CachedStatsGateway(StatsGateway):
    def __init__(self, cache_seconds: int = 60):
        self._cache_seconds = cache_seconds

    async def snapshot(self) -> KpiSnapshot:
        if _Cache.snapshot and time.monotonic() - _Cache.fetched_at < self._cache_seconds:
            return _Cache.snapshot

        snapshot = await self._fetch()
        if snapshot is None:
            # En cas de panne, on garde les derniers chiffres connus : leur heure dit qu'ils datent.
            snapshot = _Cache.snapshot or KpiSnapshot.unavailable(INJOIGNABLE)
        _Cache.snapshot = snapshot
        _Cache.fetched_at = time.monotonic()
        return snapshot

    @abstractmethod
    async def _fetch(self) -> Optional[KpiSnapshot]: ...
