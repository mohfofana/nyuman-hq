from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class GoogleIdentity:
    email: str
    name: Optional[str]


class GoogleTokenVerifier(ABC):
    """Vérifie le jeton envoyé par le bouton « Se connecter avec Google »."""

    @abstractmethod
    async def verify(self, credential: str) -> GoogleIdentity: ...
