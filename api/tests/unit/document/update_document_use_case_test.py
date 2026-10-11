from unittest.mock import AsyncMock

import pytest

from domain.entities.document import Document
from domain.entities.membre import HEAD, Membre
from use_cases.common.ports.out.transaction import Transaction
from use_cases.core.document.document_input import DocumentInput
from use_cases.core.document.exceptions.document_exceptions import (
    DocumentInvalideException,
    DocumentModifieEntreTempsException,
)
from use_cases.core.document.repository.document_repository import DocumentRepository
from use_cases.core.document.update_document_use_case import UpdateDocumentUseCase
from use_cases.core.evenement.repository.evenement_repository import EvenementRepository


def make_document(**kw) -> Document:
    base = dict(id=5, title="Pitch", category="pitch", content="v1", created_by=1, updated_by=1, version=3)
    base.update(kw)
    return Document(**base)


@pytest.fixture
def repos():
    documents = AsyncMock(spec=DocumentRepository)
    documents.save.side_effect = lambda d: d
    return documents, AsyncMock(spec=EvenementRepository), AsyncMock(spec=Transaction)


@pytest.fixture
def actor() -> Membre:
    return Membre(id=7, name="Kevin", email="kevin@example.com", role=HEAD)


async def test_nouvelle_version_avec_auteur_et_evenement(repos, actor):
    documents, evenements, transaction = repos
    documents.find_by_id.return_value = make_document()
    use_case = UpdateDocumentUseCase(documents, evenements, transaction)

    result = await use_case(actor, 5, DocumentInput("Pitch", "pitch", "v4"), base_version=3)

    assert result.version == 4 and result.updated_by == 7
    saved_version = documents.add_version.await_args.args[0]
    assert (saved_version.version, saved_version.content, saved_version.author_id) == (4, "v4", 7)
    assert "version 4" in evenements.add.await_args.args[0].text
    transaction.commit.assert_awaited_once()


async def test_refuse_d_ecraser_le_travail_d_un_autre(repos, actor):
    documents, evenements, transaction = repos
    documents.find_by_id.return_value = make_document(version=4)
    use_case = UpdateDocumentUseCase(documents, evenements, transaction)

    with pytest.raises(DocumentModifieEntreTempsException):
        await use_case(actor, 5, DocumentInput("Pitch", "pitch", "v4 bis"), base_version=3)
    transaction.commit.assert_not_awaited()


async def test_rien_ne_change_pas_de_nouvelle_version(repos, actor):
    documents, evenements, transaction = repos
    documents.find_by_id.return_value = make_document()
    use_case = UpdateDocumentUseCase(documents, evenements, transaction)

    result = await use_case(actor, 5, DocumentInput(" Pitch ", "pitch", "v1"), base_version=3)

    assert result.version == 3
    documents.add_version.assert_not_awaited()
    evenements.add.assert_not_awaited()


async def test_un_titre_vide_est_refuse(repos, actor):
    documents, evenements, transaction = repos
    with pytest.raises(DocumentInvalideException):
        await UpdateDocumentUseCase(documents, evenements, transaction)(
            actor, 5, DocumentInput("   ", "pitch", "x"), base_version=3
        )
