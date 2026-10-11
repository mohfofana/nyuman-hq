from sqlalchemy.ext.asyncio import AsyncSession

from adapters.common.ports.out.sqlalchemy_transaction import SqlAlchemyTransaction
from adapters.core.evenement.repository.evenement_repository import EvenementRepository
from adapters.core.lien.repository.lien_repository import LienRepository
from adapters.core.membre.repository.membre_repository import MembreRepository
from core.config import settings
from use_cases.core.lien.lien_use_cases import DemanderLienUseCase, ValiderLienUseCase


class LienAppConfig:
    def __init__(self, session: AsyncSession):
        self._membre_repository = MembreRepository(session)
        self._lien_repository = LienRepository(session)
        self._evenement_repository = EvenementRepository(session)
        self._transaction = SqlAlchemyTransaction(session)

    def demander_lien_use_case(self) -> DemanderLienUseCase:
        return DemanderLienUseCase(
            self._membre_repository,
            self._lien_repository,
            self._transaction,
            settings.HQ_PUBLIC_URL,
            settings.LIEN_MINUTES,
        )

    def valider_lien_use_case(self) -> ValiderLienUseCase:
        return ValiderLienUseCase(
            self._membre_repository, self._lien_repository, self._evenement_repository, self._transaction
        )
