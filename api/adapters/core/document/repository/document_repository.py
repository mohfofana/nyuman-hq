from typing import List, Optional, Tuple

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.core.document.entity.document_entity import DocumentEntity, DocumentVersionEntity
from adapters.core.document.entity.document_mapper import DocumentMapper
from adapters.core.membre.entity.membre_entity import MembreEntity
from adapters.core.membre.entity.membre_mapper import MembreMapper
from domain.entities.document import Document, DocumentVersion
from domain.entities.membre import Membre
from use_cases.core.document.repository.document_repository import DocumentRepository as DocumentRepositoryInterface


def _like_pattern(query: str) -> str:
    # Les caractères spéciaux de LIKE sont échappés : « 100% » cherche bien « 100% ».
    escaped = query.lower().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


class DocumentRepository(DocumentRepositoryInterface):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, document: Document) -> Document:
        entity = await self._session.get(DocumentEntity, document.id) if document.id else None
        if entity is None:
            entity = DocumentEntity()
            self._session.add(entity)
        DocumentMapper.apply(document, entity)
        await self._session.flush()
        return DocumentMapper.to_domain(entity)

    async def find_by_id(self, document_id: int) -> Optional[Document]:
        entity = await self._session.get(DocumentEntity, document_id)
        return DocumentMapper.to_domain(entity) if entity else None

    async def find_by_title(self, title: str) -> Optional[Document]:
        result = await self._session.execute(select(DocumentEntity).where(DocumentEntity.title == title).limit(1))
        entity = result.scalar_one_or_none()
        return DocumentMapper.to_domain(entity) if entity else None

    async def search(self, category: Optional[str], query: Optional[str], archived: bool) -> List[Document]:
        stmt = select(DocumentEntity).where(DocumentEntity.archived.is_(archived))
        if category:
            stmt = stmt.where(DocumentEntity.category == category)
        if query:
            pattern = _like_pattern(query)
            stmt = stmt.where(
                or_(
                    func.lower(DocumentEntity.title).like(pattern, escape="\\"),
                    func.lower(DocumentEntity.content).like(pattern, escape="\\"),
                )
            )
        result = await self._session.execute(stmt.order_by(DocumentEntity.updated_at.desc()))
        return [DocumentMapper.to_domain(e) for e in result.scalars().all()]

    async def add_version(self, version: DocumentVersion) -> None:
        self._session.add(DocumentMapper.version_to_entity(version))
        await self._session.flush()

    async def find_versions(self, document_id: int) -> List[Tuple[DocumentVersion, Membre]]:
        result = await self._session.execute(
            select(DocumentVersionEntity, MembreEntity)
            .join(MembreEntity, MembreEntity.id == DocumentVersionEntity.author_id)
            .where(DocumentVersionEntity.document_id == document_id)
            .order_by(DocumentVersionEntity.version.desc())
        )
        return [(DocumentMapper.version_to_domain(v), MembreMapper.to_domain(m)) for v, m in result.all()]

    async def find_version(self, document_id: int, version: int) -> Optional[Tuple[DocumentVersion, Membre]]:
        result = await self._session.execute(
            select(DocumentVersionEntity, MembreEntity)
            .join(MembreEntity, MembreEntity.id == DocumentVersionEntity.author_id)
            .where(DocumentVersionEntity.document_id == document_id, DocumentVersionEntity.version == version)
        )
        row = result.first()
        return (DocumentMapper.version_to_domain(row[0]), MembreMapper.to_domain(row[1])) if row else None
