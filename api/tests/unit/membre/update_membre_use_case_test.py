from unittest.mock import AsyncMock

import pytest

from domain.entities.membre import AGENT, HEAD, MEMBRE, Membre
from use_cases.common.ports.out.transaction import Transaction
from use_cases.core.membre.exceptions.membre_exceptions import (
    ModificationInterditeException,
    ReserveAuxHeadsException,
)
from use_cases.core.membre.repository.membre_repository import MembreRepository
from use_cases.core.membre.update_membre_use_case import UpdateMembreUseCase

HEAD_ACTOR = Membre(id=1, name="Fondateur", email="f@example.com", role=HEAD)


@pytest.fixture
def membres() -> AsyncMock:
    repo = AsyncMock(spec=MembreRepository)
    repo.save.side_effect = lambda m: m
    return repo


@pytest.fixture
def use_case(membres) -> UpdateMembreUseCase:
    return UpdateMembreUseCase(membres, AsyncMock(spec=Transaction))


async def test_la_maison_garde_au_moins_un_head(use_case, membres):
    membres.find_by_id.return_value = Membre(id=2, name="Kevin", email="k@example.com", role=HEAD)
    membres.count_active_heads.return_value = 1
    with pytest.raises(ModificationInterditeException):
        await use_case(HEAD_ACTOR, 2, role=MEMBRE)


async def test_un_head_peut_en_retirer_un_autre_s_il_en_reste(use_case, membres):
    membres.find_by_id.return_value = Membre(id=2, name="Kevin", email="k@example.com", role=HEAD)
    membres.count_active_heads.return_value = 2
    result = await use_case(HEAD_ACTOR, 2, role=MEMBRE)
    assert result.role == MEMBRE


async def test_un_membre_ne_change_pas_les_droits(use_case):
    with pytest.raises(ReserveAuxHeadsException):
        await use_case(Membre(id=3, name="Awa", email="a@example.com", role=MEMBRE), 2, role=HEAD)


async def test_les_agents_ne_se_reglent_pas_ici(use_case, membres):
    membres.find_by_id.return_value = Membre(id=9, name="Contradicteur", kind=AGENT)
    with pytest.raises(ModificationInterditeException):
        await use_case(HEAD_ACTOR, 9, active=False)
