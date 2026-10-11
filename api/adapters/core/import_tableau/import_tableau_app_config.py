from sqlalchemy.ext.asyncio import AsyncSession

from adapters.core.decision.decision_app_config import DecisionAppConfig
from adapters.core.document.repository.document_repository import DocumentRepository
from adapters.core.pro.pro_app_config import ProAppConfig
from adapters.core.tache.tache_app_config import TacheAppConfig
from use_cases.common.ports.out.tableur_reader import TableurReader
from use_cases.core.import_tableau.import_tableau_use_case import ImportTableauUseCase


class ImportTableauAppConfig:
    def __init__(self, session: AsyncSession, reader: TableurReader):
        # Une seule session : tout l'import part dans la même transaction, ou rien.
        self._taches = TacheAppConfig(session)
        self._decisions = DecisionAppConfig(session)
        self._pros = ProAppConfig(session)
        self._documents = DocumentRepository(session)
        self._reader = reader

    def import_tableau_use_case(self) -> ImportTableauUseCase:
        return ImportTableauUseCase(
            reader=self._reader,
            taches=self._taches.tache_repository,
            etapes=self._taches.etape_repository,
            decisions=self._decisions.decision_repository,
            pros=self._pros.pro_repository,
            documents=self._documents,
            membres=self._taches.membre_repository,
            evenements=self._taches.evenement_repository,
            transaction=self._taches.transaction,
            create_tache=self._taches.create_tache_use_case(),
            add_etape=self._taches.add_etape_use_case(),
            create_decision=self._decisions.create_decision_use_case(),
            create_pro=self._pros.create_pro_use_case(),
        )
