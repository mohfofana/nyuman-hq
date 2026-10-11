from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.core.document.contract.document_view_model import (
    CreateDocumentRequest,
    DocumentSummaryViewModel,
    DocumentVersionFullViewModel,
    DocumentVersionViewModel,
    DocumentViewModel,
    UpdateDocumentRequest,
)
from adapters.core.document.document_app_config import DocumentAppConfig
from adapters.core.membre.membre_app_config import MembreAppConfig
from core.database import get_async_session
from core.session.session_middleware import get_current_membre
from domain.entities.membre import Membre

document_router = APIRouter(prefix="/api/documents", tags=["Bibliothèque"])


class DocumentController:
    def __init__(self, session: AsyncSession):
        self.config = DocumentAppConfig(session)
        self._membres = MembreAppConfig(session)

    async def membres(self) -> Dict[int, Membre]:
        # L'équipe tient en quelques dizaines de membres : on charge tout pour afficher les auteurs.
        return {m.id: m for m in await self._membres.get_membre_list_use_case()()}


def document_controller(session: AsyncSession = Depends(get_async_session)) -> DocumentController:
    return DocumentController(session)


@document_router.get("", response_model=List[DocumentSummaryViewModel])
async def list_documents(
    categorie: Optional[str] = Query(default=None, max_length=30),
    q: Optional[str] = Query(default=None, max_length=200),
    archives: bool = False,
    controller: DocumentController = Depends(document_controller),
) -> List[DocumentSummaryViewModel]:
    documents = await controller.config.get_document_list_use_case()(categorie, q, archives)
    membres = await controller.membres()
    return [DocumentSummaryViewModel.of(d, membres) for d in documents]


@document_router.post("", response_model=DocumentViewModel, status_code=201)
async def create_document(
    request: CreateDocumentRequest,
    actor: Membre = Depends(get_current_membre),
    controller: DocumentController = Depends(document_controller),
) -> DocumentViewModel:
    document = await controller.config.create_document_use_case()(actor, request.to_input())
    return DocumentViewModel.of(document, await controller.membres())


@document_router.get("/{document_id}", response_model=DocumentViewModel)
async def get_document(
    document_id: int, controller: DocumentController = Depends(document_controller)
) -> DocumentViewModel:
    document = await controller.config.get_document_by_id_use_case()(document_id)
    return DocumentViewModel.of(document, await controller.membres())


@document_router.put("/{document_id}", response_model=DocumentViewModel)
async def update_document(
    document_id: int,
    request: UpdateDocumentRequest,
    actor: Membre = Depends(get_current_membre),
    controller: DocumentController = Depends(document_controller),
) -> DocumentViewModel:
    document = await controller.config.update_document_use_case()(
        actor, document_id, request.to_input(), request.base_version
    )
    return DocumentViewModel.of(document, await controller.membres())


@document_router.post("/{document_id}/archiver", response_model=DocumentViewModel)
async def archive_document(
    document_id: int,
    actor: Membre = Depends(get_current_membre),
    controller: DocumentController = Depends(document_controller),
) -> DocumentViewModel:
    document = await controller.config.archive_document_use_case()(actor, document_id, archived=True)
    return DocumentViewModel.of(document, await controller.membres())


@document_router.post("/{document_id}/restaurer", response_model=DocumentViewModel)
async def restore_document(
    document_id: int,
    actor: Membre = Depends(get_current_membre),
    controller: DocumentController = Depends(document_controller),
) -> DocumentViewModel:
    document = await controller.config.archive_document_use_case()(actor, document_id, archived=False)
    return DocumentViewModel.of(document, await controller.membres())


@document_router.get("/{document_id}/versions", response_model=List[DocumentVersionViewModel])
async def list_versions(
    document_id: int, controller: DocumentController = Depends(document_controller)
) -> List[DocumentVersionViewModel]:
    versions = await controller.config.get_document_version_list_use_case()(document_id)
    return [DocumentVersionViewModel.of(v, author) for v, author in versions]


@document_router.get("/{document_id}/versions/{version}", response_model=DocumentVersionFullViewModel)
async def get_version(
    document_id: int, version: int, controller: DocumentController = Depends(document_controller)
) -> DocumentVersionFullViewModel:
    found, author = await controller.config.get_document_version_use_case()(document_id, version)
    return DocumentVersionFullViewModel.of(found, author)
