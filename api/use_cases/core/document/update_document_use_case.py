from datetime import datetime, timezone

from domain.entities.document import Document, DocumentVersion
from domain.entities.evenement import Evenement
from domain.entities.membre import Membre
from use_cases.common.ports.out.transaction import Transaction
from use_cases.core.document.document_input import DocumentInput
from use_cases.core.document.exceptions.document_exceptions import (
    DocumentArchiveException,
    DocumentModifieEntreTempsException,
    DocumentNotFoundException,
)
from use_cases.core.document.repository.document_repository import DocumentRepository
from use_cases.core.evenement.repository.evenement_repository import EvenementRepository


class UpdateDocumentUseCase:
    """Enregistre une nouvelle version. Si quelqu'un a enregistré entre-temps, on refuse au lieu d'écraser son travail."""

    def __init__(
        self,
        document_repository: DocumentRepository,
        evenement_repository: EvenementRepository,
        transaction: Transaction,
    ):
        self._document_repository = document_repository
        self._evenement_repository = evenement_repository
        self._transaction = transaction

    async def __call__(self, actor: Membre, document_id: int, data: DocumentInput, base_version: int) -> Document:
        data = data.validated()
        document = await self._document_repository.find_by_id(document_id)
        if document is None:
            raise DocumentNotFoundException()
        if document.archived:
            raise DocumentArchiveException()
        if document.version != base_version:
            raise DocumentModifieEntreTempsException()

        unchanged = (document.title, document.category, document.content) == (data.title, data.category, data.content)
        if unchanged:
            return document

        document.title = data.title
        document.category = data.category
        document.content = data.content
        document.version += 1
        document.updated_by = actor.id
        document.updated_at = datetime.now(timezone.utc)
        document = await self._document_repository.save(document)
        await self._document_repository.add_version(
            DocumentVersion(
                document_id=document.id,
                version=document.version,
                title=document.title,
                category=document.category,
                content=document.content,
                author_id=actor.id,
            )
        )
        await self._evenement_repository.add(
            Evenement(
                actor_id=actor.id,
                verb="document_modifie",
                text=f"a modifié le document « {document.title} » (version {document.version}).",
                link=f"/bibliotheque/{document.id}",
            )
        )
        await self._transaction.commit()
        return document
