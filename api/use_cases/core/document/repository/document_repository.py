from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

from domain.entities.document import Document, DocumentVersion
from domain.entities.membre import Membre


class DocumentRepository(ABC):
    @abstractmethod
    async def save(self, document: Document) -> Document: ...

    @abstractmethod
    async def find_by_id(self, document_id: int) -> Optional[Document]: ...

    @abstractmethod
    async def search(self, category: Optional[str], query: Optional[str], archived: bool) -> List[Document]: ...

    @abstractmethod
    async def add_version(self, version: DocumentVersion) -> None: ...

    @abstractmethod
    async def find_versions(self, document_id: int) -> List[Tuple[DocumentVersion, Membre]]: ...

    @abstractmethod
    async def find_version(self, document_id: int, version: int) -> Optional[Tuple[DocumentVersion, Membre]]: ...

    @abstractmethod
    async def find_by_title(self, title: str) -> Optional[Document]: ...
