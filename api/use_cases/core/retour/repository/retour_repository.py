from abc import ABC, abstractmethod
from typing import List, Optional

from domain.entities.retour import Retour


class RetourRepository(ABC):
    @abstractmethod
    async def save(self, retour: Retour) -> Retour: ...

    @abstractmethod
    async def find_by_id(self, retour_id: int) -> Optional[Retour]: ...

    @abstractmethod
    async def known_asc_ids(self) -> set: ...

    @abstractmethod
    async def search(self, statut: Optional[str]) -> List[Retour]: ...

    @abstractmethod
    async def count(self, statut: str) -> int: ...
