from domain.entities.document import Document, DocumentVersion
from domain.entities.evenement import Evenement
from domain.entities.membre import Membre
from use_cases.common.ports.out.transaction import Transaction
from use_cases.core.document.document_input import DocumentInput
from use_cases.core.document.repository.document_repository import DocumentRepository
from use_cases.core.evenement.repository.evenement_repository import EvenementRepository


class CreateDocumentUseCase:
    def __init__(
        self,
        document_repository: DocumentRepository,
        evenement_repository: EvenementRepository,
        transaction: Transaction,
    ):
        self._document_repository = document_repository
        self._evenement_repository = evenement_repository
        self._transaction = transaction

    async def __call__(self, actor: Membre, data: DocumentInput) -> Document:
        data = data.validated()
        document = await self._document_repository.save(
            Document(
                title=data.title,
                category=data.category,
                content=data.content,
                created_by=actor.id,
                updated_by=actor.id,
            )
        )
        await self._document_repository.add_version(
            DocumentVersion(
                document_id=document.id,
                version=1,
                title=document.title,
                category=document.category,
                content=document.content,
                author_id=actor.id,
            )
        )
        await self._evenement_repository.add(
            Evenement(
                actor_id=actor.id,
                verb="document_cree",
                text=f"a créé le document « {document.title} ».",
                link=f"/bibliotheque/{document.id}",
            )
        )
        await self._transaction.commit()
        return document
