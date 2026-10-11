from abc import ABC, abstractmethod
from typing import List, Optional

from domain.entities.membre import Membre


class MembreRepository(ABC):
    @abstractmethod
    async def save(self, membre: Membre) -> Membre: ...

    @abstractmethod
    async def find_by_id(self, membre_id: int) -> Optional[Membre]: ...

    @abstractmethod
    async def find_by_email(self, email: str) -> Optional[Membre]: ...

    @abstractmethod
    async def find_all(self) -> List[Membre]: ...

    @abstractmethod
    async def count_active_heads(self) -> int: ...

    @abstractmethod
    async def count_humans(self) -> int: ...
