from abc import ABC, abstractmethod
from typing import Optional

from domain.entities.objectif import Objectif


class ObjectifRepository(ABC):
    @abstractmethod
    async def save(self, objectif: Objectif) -> Objectif: ...

    @abstractmethod
    async def find_by_id(self, objectif_id: int) -> Optional[Objectif]: ...

    @abstractmethod
    async def find_latest(self, pole: str = "") -> Optional[Objectif]:
        """Le dernier objectif de toute la maison (pôle vide) ou d'un pôle."""
