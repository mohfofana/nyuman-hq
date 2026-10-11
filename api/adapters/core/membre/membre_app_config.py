from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from adapters.common.ports.out.sqlalchemy_transaction import SqlAlchemyTransaction
from adapters.core.evenement.repository.evenement_repository import EvenementRepository
from adapters.core.membre.repository.membre_repository import MembreRepository
from use_cases.common.ports.out.google_token_verifier import GoogleTokenVerifier
from use_cases.core.membre.add_membre_use_case import AddMembreUseCase
from use_cases.core.membre.get_membre_by_id_use_case import GetMembreByIdUseCase
from use_cases.core.membre.get_membre_list_use_case import GetMembreListUseCase
from use_cases.core.membre.login_dev_use_case import LoginDevUseCase
from use_cases.core.membre.login_with_google_use_case import LoginWithGoogleUseCase
from use_cases.core.membre.mark_presence_use_case import MarkPresenceUseCase
from use_cases.core.membre.update_membre_use_case import UpdateMembreUseCase


class MembreAppConfig:
    def __init__(self, session: AsyncSession, verifier: Optional[GoogleTokenVerifier] = None):
        self._membre_repository = MembreRepository(session)
        self._evenement_repository = EvenementRepository(session)
        self._transaction = SqlAlchemyTransaction(session)
        self._verifier = verifier

    def login_with_google_use_case(self) -> LoginWithGoogleUseCase:
        assert self._verifier is not None
        return LoginWithGoogleUseCase(
            self._verifier, self._membre_repository, self._evenement_repository, self._transaction
        )

    def login_dev_use_case(self) -> LoginDevUseCase:
        return LoginDevUseCase(self._membre_repository, self._transaction)

    def get_membre_by_id_use_case(self) -> GetMembreByIdUseCase:
        return GetMembreByIdUseCase(self._membre_repository)

    def get_membre_list_use_case(self) -> GetMembreListUseCase:
        return GetMembreListUseCase(self._membre_repository)

    def mark_presence_use_case(self) -> MarkPresenceUseCase:
        return MarkPresenceUseCase(self._membre_repository, self._transaction)

    def add_membre_use_case(self) -> AddMembreUseCase:
        return AddMembreUseCase(self._membre_repository, self._evenement_repository, self._transaction)

    def update_membre_use_case(self) -> UpdateMembreUseCase:
        return UpdateMembreUseCase(self._membre_repository, self._transaction)
