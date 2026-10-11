from typing import List, Optional, Tuple

from domain.entities.evenement import Evenement
from domain.entities.membre import Membre
from use_cases.core.evenement.repository.evenement_repository import EvenementRepository


class GetEvenementListUseCase:
    def __init__(self, evenement_repository: EvenementRepository):
        self._evenement_repository = evenement_repository

    async def __call__(self, limit: int = 30, actor_id: Optional[int] = None) -> List[Tuple[Evenement, Membre]]:
        return await self._evenement_repository.find_latest(min(limit, 100), actor_id)
