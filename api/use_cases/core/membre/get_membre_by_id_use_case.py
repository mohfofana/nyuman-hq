from typing import Optional

from domain.entities.membre import Membre
from use_cases.core.membre.repository.membre_repository import MembreRepository


class GetMembreByIdUseCase:
    def __init__(self, membre_repository: MembreRepository):
        self._membre_repository = membre_repository

    async def __call__(self, membre_id: int) -> Optional[Membre]:
        return await self._membre_repository.find_by_id(membre_id)
