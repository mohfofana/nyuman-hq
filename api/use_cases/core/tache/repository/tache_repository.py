from abc import ABC, abstractmethod
from typing import List, Optional

from domain.entities.tache import Tache


class TacheRepository(ABC):
    @abstractmethod
    async def save(self, tache: Tache) -> Tache: ...

    @abstractmethod
    async def find_by_id(self, tache_id: int) -> Optional[Tache]: ...

    @abstractmethod
    async def search(self, assignee_id: Optional[int], archived: bool) -> List[Tache]: ...

    @abstractmethod
    async def find_by_ref(self, ref_externe: str) -> Optional[Tache]: ...

    @abstractmethod
    async def max_position(self, status: str) -> float: ...
