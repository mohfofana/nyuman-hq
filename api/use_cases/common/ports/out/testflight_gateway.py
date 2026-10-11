from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Tuple


@dataclass
class RetourSource:
    """Un retour tel que le donne App Store Connect, avant d'être rangé dans HQ."""

    asc_id: str
    kind: str  # « capture » ou « plantage »
    created_at: datetime
    comment: str = ""
    email: Optional[str] = None
    device_model: str = ""
    os_version: str = ""
    locale: str = ""
    build_version: str = ""
    screenshot_urls: List[str] = field(default_factory=list)


class TestflightGateway(ABC):
    """Lit les retours des testeurs TestFlight (API App Store Connect)."""

    @property
    @abstractmethod
    def configured(self) -> bool: ...

    @abstractmethod
    async def fetch(self, limit: int = 50) -> List[RetourSource]: ...

    @abstractmethod
    async def download(self, url: str) -> Tuple[bytes, str]:
        """Renvoie le contenu de l'image et son type (image/jpeg…). Les liens d'Apple expirent vite."""


class CaptureStorage(ABC):
    """Garde les captures d'écran des testeurs sur le disque de HQ."""

    @abstractmethod
    def save(self, name: str, content: bytes) -> str: ...

    @abstractmethod
    def path(self, name: str): ...
