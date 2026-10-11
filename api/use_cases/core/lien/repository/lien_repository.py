from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from domain.entities.lien_connexion import LienConnexion


class LienRepository(ABC):
    @abstractmethod
    async def add(self, lien: LienConnexion) -> LienConnexion: ...

    @abstractmethod
    async def find_by_hash(self, token_hash: str) -> Optional[LienConnexion]: ...

    @abstractmethod
    async def count_since(self, membre_id: int, since: datetime) -> int: ...

    @abstractmethod
    async def consommer(self, lien_id: int, now: datetime) -> bool:
        """Marque le lien comme utilisé, seulement s'il ne l'était pas déjà. Renvoie False sinon."""

    @abstractmethod
    async def annuler_restants(self, membre_id: int, now: datetime) -> None: ...

    @abstractmethod
    async def purger(self, before: datetime) -> None: ...
