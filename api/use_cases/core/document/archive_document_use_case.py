from datetime import datetime, timezone

from domain.entities.document import Document
from domain.entities.evenement import Evenement
from domain.entities.membre import Membre
from use_cases.common.ports.out.transaction import Transaction
from use_cases.core.document.exceptions.document_exceptions import DocumentNotFoundException
from use_cases.core.document.repository.document_repository import DocumentRepository
from use_cases.core.evenement.repository.evenement_repository import EvenementRepository


class ArchiveDocumentUseCase:
    """Met un document à la corbeille, ou l'en sort. Un document n'est jamais supprimé définitivement."""

    def __init__(
        self,
        document_repository: DocumentRepository,
        evenement_repository: EvenementRepository,
        transaction: Transaction,
    ):
        self._document_repository = document_repository
        self._evenement_repository = evenement_repository
        self._transaction = transaction

    async def __call__(self, actor: Membre, document_id: int, archived: bool) -> Document:
        document = await self._document_repository.find_by_id(document_id)
        if document is None:
            raise DocumentNotFoundException()
        if document.archived == archived:
            return document
        document.archived = archived
        document.updated_by = actor.id
        document.updated_at = datetime.now(timezone.utc)
        document = await self._document_repository.save(document)
        action = "a mis à la corbeille" if archived else "a restauré"
        await self._evenement_repository.add(
            Evenement(
                actor_id=actor.id,
                verb="document_archive" if archived else "document_restaure",
                text=f"{action} le document « {document.title} ».",
                link=f"/bibliotheque/{document.id}",
            )
        )
        await self._transaction.commit()
        return document
