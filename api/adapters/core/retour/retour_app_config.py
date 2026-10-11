from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from adapters.common.ports.out.sqlalchemy_transaction import SqlAlchemyTransaction
from adapters.core.evenement.repository.evenement_repository import EvenementRepository
from adapters.core.retour.repository.retour_repository import RetourRepository
from adapters.core.tache.tache_app_config import TacheAppConfig
from use_cases.common.ports.out.testflight_gateway import CaptureStorage, TestflightGateway
from use_cases.core.retour.retour_use_cases import (
    ClasserRetourUseCase,
    ConvertRetourUseCase,
    CreateRetourUseCase,
    GetRetourByIdUseCase,
    GetRetourListUseCase,
    SyncRetoursUseCase,
)


class TestflightState:
    """Heure de la dernière synchronisation TestFlight (en mémoire, affichée dans les réglages)."""

    derniere_synchro: Optional[datetime] = None
    derniere_erreur: Optional[str] = None


class RetourAppConfig:
    def __init__(self, session: AsyncSession, storage: CaptureStorage, gateway: TestflightGateway):
        self.retour_repository = RetourRepository(session)
        self._evenement_repository = EvenementRepository(session)
        self._transaction = SqlAlchemyTransaction(session)
        self._taches = TacheAppConfig(session)
        self.storage = storage
        self.gateway = gateway

    def create_retour_use_case(self) -> CreateRetourUseCase:
        return CreateRetourUseCase(self.retour_repository, self.storage, self._evenement_repository, self._transaction)

    def sync_retours_use_case(self) -> SyncRetoursUseCase:
        return SyncRetoursUseCase(self.gateway, self.retour_repository, self.storage, self._transaction)

    def get_retour_list_use_case(self) -> GetRetourListUseCase:
        return GetRetourListUseCase(self.retour_repository)

    def get_retour_by_id_use_case(self) -> GetRetourByIdUseCase:
        return GetRetourByIdUseCase(self.retour_repository)

    def convert_retour_use_case(self) -> ConvertRetourUseCase:
        return ConvertRetourUseCase(
            self.retour_repository, self._taches.create_tache_use_case(), self._evenement_repository, self._transaction
        )

    def classer_retour_use_case(self) -> ClasserRetourUseCase:
        return ClasserRetourUseCase(self.retour_repository, self._transaction)
