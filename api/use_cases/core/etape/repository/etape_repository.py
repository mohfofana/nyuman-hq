from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from domain.entities.etape import Etape


class EtapeRepository(ABC):
    @abstractmethod
    async def save(self, etape: Etape) -> Etape: ...

    @abstractmethod
    async def find_by_id(self, etape_id: int) -> Optional[Etape]: ...

    @abstractmethod
    async def find_by_ref(self, ref_externe: str) -> Optional[Etape]: ...

    @abstractmethod
    async def list_for(self, tache_ids: List[int]) -> Dict[int, List[Etape]]:
        """Les sous-étapes actives de ces tâches, dans l'ordre."""

    @abstractmethod
    async def max_position(self, tache_id: int) -> float: ...
