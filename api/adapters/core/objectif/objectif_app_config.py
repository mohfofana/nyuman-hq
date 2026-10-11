from sqlalchemy.ext.asyncio import AsyncSession

from adapters.common.ports.out.sqlalchemy_transaction import SqlAlchemyTransaction
from adapters.core.evenement.repository.evenement_repository import EvenementRepository
from adapters.core.objectif.repository.objectif_repository import ObjectifRepository
from use_cases.common.ports.out.stats_gateway import StatsGateway
from use_cases.core.objectif.get_current_objectif_use_case import GetCurrentObjectifUseCase, GetPoleObjectifsUseCase
from use_cases.core.objectif.save_current_objectif_use_case import SaveCurrentObjectifUseCase, UpdateAvancementUseCase


class ObjectifAppConfig:
    def __init__(self, session: AsyncSession, stats_gateway: StatsGateway):
        self._objectif_repository = ObjectifRepository(session)
        self._evenement_repository = EvenementRepository(session)
        self._transaction = SqlAlchemyTransaction(session)
        self._stats_gateway = stats_gateway

    def get_current_objectif_use_case(self) -> GetCurrentObjectifUseCase:
        return GetCurrentObjectifUseCase(self._objectif_repository, self._stats_gateway)

    def get_pole_objectifs_use_case(self) -> GetPoleObjectifsUseCase:
        return GetPoleObjectifsUseCase(self.get_current_objectif_use_case())

    def save_current_objectif_use_case(self) -> SaveCurrentObjectifUseCase:
        return SaveCurrentObjectifUseCase(self._objectif_repository, self._evenement_repository, self._transaction)

    def update_avancement_use_case(self) -> UpdateAvancementUseCase:
        return UpdateAvancementUseCase(self._objectif_repository, self._evenement_repository, self._transaction)
