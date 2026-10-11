from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

CATEGORIES = ("cerveau", "contrats", "finances", "comptes-rendus", "specs", "pitch", "autre")


@dataclass
class Document:
    """Un document de la bibliothèque. Chaque enregistrement crée une nouvelle version ; rien n'est effacé."""

    title: str
    category: str
    content: str
    created_by: int
    updated_by: int
    version: int = 1
    archived: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    id: Optional[int] = None


@dataclass
class DocumentVersion:
    document_id: int
    version: int
    title: str
    category: str
    content: str
    author_id: int
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    id: Optional[int] = None
