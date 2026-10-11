from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

from domain.entities.evenement import Evenement
from domain.entities.membre import Membre


class EvenementRepository(ABC):
    @abstractmethod
    async def add(self, evenement: Evenement) -> None: ...

    @abstractmethod
    async def find_latest(self, limit: int, actor_id: Optional[int] = None) -> List[Tuple[Evenement, Membre]]: ...
