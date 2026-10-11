from abc import ABC, abstractmethod

from domain.value_objects.kpi import KpiSnapshot


class StatsGateway(ABC):
    """Lit les totaux de l'app Nyuman (route statistiques de nyuman-api, en lecture seule)."""

    @abstractmethod
    async def snapshot(self) -> KpiSnapshot: ...
