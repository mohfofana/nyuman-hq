from typing import List, Optional, Tuple

from domain.entities.document import Document, DocumentVersion
from domain.entities.membre import Membre
from use_cases.core.document.exceptions.document_exceptions import (
    DocumentNotFoundException,
    DocumentVersionNotFoundException,
)
from use_cases.core.document.repository.document_repository import DocumentRepository


class GetDocumentListUseCase:
    def __init__(self, document_repository: DocumentRepository):
        self._document_repository = document_repository

    async def __call__(self, category: Optional[str], query: Optional[str], archived: bool) -> List[Document]:
        query = query.strip() if query else None
        return await self._document_repository.search(category, query or None, archived)


class GetDocumentByIdUseCase:
    def __init__(self, document_repository: DocumentRepository):
        self._document_repository = document_repository

    async def __call__(self, document_id: int) -> Document:
        document = await self._document_repository.find_by_id(document_id)
        if document is None:
            raise DocumentNotFoundException()
        return document


class GetDocumentVersionListUseCase:
    def __init__(self, document_repository: DocumentRepository):
        self._document_repository = document_repository

    async def __call__(self, document_id: int) -> List[Tuple[DocumentVersion, Membre]]:
        if await self._document_repository.find_by_id(document_id) is None:
            raise DocumentNotFoundException()
        return await self._document_repository.find_versions(document_id)


class GetDocumentVersionUseCase:
    def __init__(self, document_repository: DocumentRepository):
        self._document_repository = document_repository

    async def __call__(self, document_id: int, version: int) -> Tuple[DocumentVersion, Membre]:
        found = await self._document_repository.find_version(document_id, version)
        if found is None:
            raise DocumentVersionNotFoundException()
        return found
