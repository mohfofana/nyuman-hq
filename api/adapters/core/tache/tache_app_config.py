from sqlalchemy.ext.asyncio import AsyncSession

from adapters.common.ports.out.sqlalchemy_transaction import SqlAlchemyTransaction
from adapters.core.etape.repository.etape_repository import EtapeRepository
from adapters.core.evenement.repository.evenement_repository import EvenementRepository
from adapters.core.membre.repository.membre_repository import MembreRepository
from adapters.core.objectif.repository.objectif_repository import ObjectifRepository
from adapters.core.tache.repository.tache_repository import TacheRepository
from use_cases.core.etape.etape_use_cases import AddEtapeUseCase, ArchiveEtapeUseCase, UpdateEtapeUseCase
from use_cases.core.tache.tache_use_cases import (
    ArchiveTacheUseCase,
    CreateTacheUseCase,
    GetTacheListUseCase,
    UpdateTacheUseCase,
)


class TacheAppConfig:
    def __init__(self, session: AsyncSession):
        self.tache_repository = TacheRepository(session)
        self.etape_repository = EtapeRepository(session)
        self.membre_repository = MembreRepository(session)
        self._objectif_repository = ObjectifRepository(session)
        self.evenement_repository = EvenementRepository(session)
        self.transaction = SqlAlchemyTransaction(session)

    def _deps(self):
        return (self.tache_repository, self.membre_repository, self._objectif_repository, self.evenement_repository, self.transaction)

    def create_tache_use_case(self) -> CreateTacheUseCase:
        return CreateTacheUseCase(*self._deps())

    def update_tache_use_case(self) -> UpdateTacheUseCase:
        return UpdateTacheUseCase(*self._deps())

    def archive_tache_use_case(self) -> ArchiveTacheUseCase:
        return ArchiveTacheUseCase(*self._deps())

    def get_tache_list_use_case(self) -> GetTacheListUseCase:
        return GetTacheListUseCase(self.tache_repository)

    def _etape_deps(self):
        return (self.tache_repository, self.etape_repository, self.membre_repository, self.transaction)

    def add_etape_use_case(self) -> AddEtapeUseCase:
        return AddEtapeUseCase(*self._etape_deps())

    def update_etape_use_case(self) -> UpdateEtapeUseCase:
        return UpdateEtapeUseCase(*self._etape_deps())

    def archive_etape_use_case(self) -> ArchiveEtapeUseCase:
        return ArchiveEtapeUseCase(*self._etape_deps())
