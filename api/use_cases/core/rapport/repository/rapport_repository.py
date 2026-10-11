from abc import ABC, abstractmethod
from typing import List, Optional

from domain.entities.rapport import Rapport


class RapportRepository(ABC):
    @abstractmethod
    async def save(self, rapport: Rapport) -> Rapport: ...

    @abstractmethod
    async def find_by_author_week(self, author_id: int, week: str) -> Optional[Rapport]: ...

    @abstractmethod
    async def list_by_author(self, author_id: int, limit: int) -> List[Rapport]: ...

    @abstractmethod
    async def list_by_week(self, week: str) -> List[Rapport]: ...
