from sqlalchemy.ext.asyncio import AsyncSession

from adapters.common.ports.out.sqlalchemy_transaction import SqlAlchemyTransaction
from adapters.core.document.repository.document_repository import DocumentRepository
from adapters.core.evenement.repository.evenement_repository import EvenementRepository
from use_cases.core.document.archive_document_use_case import ArchiveDocumentUseCase
from use_cases.core.document.create_document_use_case import CreateDocumentUseCase
from use_cases.core.document.get_document_use_cases import (
    GetDocumentByIdUseCase,
    GetDocumentListUseCase,
    GetDocumentVersionListUseCase,
    GetDocumentVersionUseCase,
)
from use_cases.core.document.update_document_use_case import UpdateDocumentUseCase


class DocumentAppConfig:
    def __init__(self, session: AsyncSession):
        self._document_repository = DocumentRepository(session)
        self._evenement_repository = EvenementRepository(session)
        self._transaction = SqlAlchemyTransaction(session)

    def get_document_list_use_case(self) -> GetDocumentListUseCase:
        return GetDocumentListUseCase(self._document_repository)

    def get_document_by_id_use_case(self) -> GetDocumentByIdUseCase:
        return GetDocumentByIdUseCase(self._document_repository)

    def create_document_use_case(self) -> CreateDocumentUseCase:
        return CreateDocumentUseCase(self._document_repository, self._evenement_repository, self._transaction)

    def update_document_use_case(self) -> UpdateDocumentUseCase:
        return UpdateDocumentUseCase(self._document_repository, self._evenement_repository, self._transaction)

    def archive_document_use_case(self) -> ArchiveDocumentUseCase:
        return ArchiveDocumentUseCase(self._document_repository, self._evenement_repository, self._transaction)

    def get_document_version_list_use_case(self) -> GetDocumentVersionListUseCase:
        return GetDocumentVersionListUseCase(self._document_repository)

    def get_document_version_use_case(self) -> GetDocumentVersionUseCase:
        return GetDocumentVersionUseCase(self._document_repository)
