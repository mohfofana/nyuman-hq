from typing import List

from domain.entities.membre import Membre
from use_cases.core.membre.repository.membre_repository import MembreRepository


class GetMembreListUseCase:
    def __init__(self, membre_repository: MembreRepository):
        self._membre_repository = membre_repository

    async def __call__(self) -> List[Membre]:
        return await self._membre_repository.find_all()
