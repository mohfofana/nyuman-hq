from sqlalchemy.ext.asyncio import AsyncSession

from adapters.common.ports.out.sqlalchemy_transaction import SqlAlchemyTransaction
from adapters.core.evenement.repository.evenement_repository import EvenementRepository
from adapters.core.membre.repository.membre_repository import MembreRepository
from adapters.core.pro.repository.pro_repository import ProRepository
from use_cases.core.pro.pro_use_cases import ArchiveProUseCase, CreateProUseCase, GetProListUseCase, UpdateProUseCase


class ProAppConfig:
    def __init__(self, session: AsyncSession):
        self.pro_repository = ProRepository(session)
        self.membre_repository = MembreRepository(session)
        self._evenement_repository = EvenementRepository(session)
        self._transaction = SqlAlchemyTransaction(session)

    def _deps(self):
        return (self.pro_repository, self.membre_repository, self._evenement_repository, self._transaction)

    def create_pro_use_case(self) -> CreateProUseCase:
        return CreateProUseCase(*self._deps())

    def update_pro_use_case(self) -> UpdateProUseCase:
        return UpdateProUseCase(*self._deps())

    def archive_pro_use_case(self) -> ArchiveProUseCase:
        return ArchiveProUseCase(*self._deps())

    def get_pro_list_use_case(self) -> GetProListUseCase:
        return GetProListUseCase(self.pro_repository)
