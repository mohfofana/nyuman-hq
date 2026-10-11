from datetime import date
from typing import Dict, Optional, Tuple

from domain.entities.membre import POLES
from domain.entities.objectif import Objectif, SuiviObjectif
from use_cases.common.ports.out.stats_gateway import StatsGateway
from use_cases.core.objectif.repository.objectif_repository import ObjectifRepository


class GetCurrentObjectifUseCase:
    """L'objectif le plus récent (de la maison ou d'un pôle), avec sa jauge déjà calculée."""

    def __init__(self, objectif_repository: ObjectifRepository, stats_gateway: StatsGateway):
        self._objectif_repository = objectif_repository
        self._stats_gateway = stats_gateway

    async def __call__(self, today: date, pole: str = "") -> Optional[Tuple[Objectif, SuiviObjectif]]:
        objectif = await self._objectif_repository.find_latest(pole)
        if objectif is None:
            return None
        if objectif.is_manual:
            current = objectif.current_manual
        else:
            current = (await self._stats_gateway.snapshot()).value_of(objectif.metric)
        return objectif, objectif.suivi(current, today)


class GetPoleObjectifsUseCase:
    """Les objectifs en cours de chaque pôle, pour l'organigramme."""

    def __init__(self, get_current: GetCurrentObjectifUseCase):
        self._get_current = get_current

    async def __call__(self, today: date) -> Dict[str, Tuple[Objectif, SuiviObjectif]]:
        result = {}
        for pole in POLES:
            found = await self._get_current(today, pole)
            if found:
                result[pole] = found
        return result
