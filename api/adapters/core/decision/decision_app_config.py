from sqlalchemy.ext.asyncio import AsyncSession

from adapters.common.ports.out.sqlalchemy_transaction import SqlAlchemyTransaction
from adapters.core.decision.repository.decision_repository import DecisionRepository
from adapters.core.evenement.repository.evenement_repository import EvenementRepository
from adapters.core.membre.repository.membre_repository import MembreRepository
from use_cases.core.decision.decision_use_cases import (
    ArchiveDecisionUseCase,
    BilanDecisionUseCase,
    CreateDecisionUseCase,
    GetConseilUseCase,
    UpdateDecisionUseCase,
    VoteDecisionUseCase,
)


class DecisionAppConfig:
    def __init__(self, session: AsyncSession):
        self.decision_repository = DecisionRepository(session)
        self.membre_repository = MembreRepository(session)
        self._evenement_repository = EvenementRepository(session)
        self._transaction = SqlAlchemyTransaction(session)

    def _deps(self):
        return (self.decision_repository, self._evenement_repository, self._transaction)

    def create_decision_use_case(self) -> CreateDecisionUseCase:
        return CreateDecisionUseCase(*self._deps())

    def update_decision_use_case(self) -> UpdateDecisionUseCase:
        return UpdateDecisionUseCase(*self._deps())

    def vote_decision_use_case(self) -> VoteDecisionUseCase:
        return VoteDecisionUseCase(*self._deps())

    def bilan_decision_use_case(self) -> BilanDecisionUseCase:
        return BilanDecisionUseCase(*self._deps())

    def archive_decision_use_case(self) -> ArchiveDecisionUseCase:
        return ArchiveDecisionUseCase(*self._deps())

    def get_conseil_use_case(self) -> GetConseilUseCase:
        return GetConseilUseCase(self.decision_repository)
