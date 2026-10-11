from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Optional, Set

from domain.entities.etape import STATUTS_ETAPE, Etape
from domain.entities.membre import Membre
from domain.entities.tache import Tache
from use_cases.common.ports.out.transaction import Transaction
from use_cases.core.etape.repository.etape_repository import EtapeRepository
from use_cases.core.membre.repository.membre_repository import MembreRepository
from use_cases.core.tache.exceptions.tache_exceptions import TacheInvalideException, TacheNotFoundException
from use_cases.core.tache.repository.tache_repository import TacheRepository


@dataclass
class NouvelleEtape:
    title: str
    responsable_id: Optional[int] = None
    livrable: str = ""
    status: str = "a_faire"
    start_date: Optional[date] = None
    due_date: Optional[date] = None
    notes: str = ""
    ref_externe: Optional[str] = None


@dataclass
class ChangementsEtape:
    """Seuls les champs listés dans `fields` sont modifiés."""

    fields: Set[str] = field(default_factory=set)
    title: Optional[str] = None
    responsable_id: Optional[int] = None
    livrable: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[date] = None
    due_date: Optional[date] = None
    notes: Optional[str] = None
    position: Optional[float] = None


class _EtapeUseCase:
    def __init__(
        self,
        tache_repository: TacheRepository,
        etape_repository: EtapeRepository,
        membre_repository: MembreRepository,
        transaction: Transaction,
    ):
        self._taches = tache_repository
        self._etapes = etape_repository
        self._membres = membre_repository
        self._transaction = transaction

    async def _tache(self, tache_id: int) -> Tache:
        tache = await self._taches.find_by_id(tache_id)
        if tache is None or tache.archived:
            raise TacheNotFoundException()
        return tache

    async def _etape(self, tache_id: int, etape_id: int) -> Etape:
        etape = await self._etapes.find_by_id(etape_id)
        if etape is None or etape.tache_id != tache_id or etape.archived:
            raise TacheInvalideException("Cette étape n’existe pas.")
        return etape

    async def _check_responsable(self, responsable_id: Optional[int]) -> None:
        if responsable_id is None:
            return
        membre = await self._membres.find_by_id(responsable_id)
        if membre is None or not membre.active:
            raise TacheInvalideException("Cette personne ne fait pas partie de la maison.")

    async def _touch(self, tache: Tache) -> None:
        # La tâche bouge aussi : le tableau des autres se met à jour.
        tache.updated_at = datetime.now(timezone.utc)
        await self._taches.save(tache)


class AddEtapeUseCase(_EtapeUseCase):
    async def __call__(self, actor: Membre, tache_id: int, data: NouvelleEtape, commit: bool = True) -> Etape:
        tache = await self._tache(tache_id)
        title = data.title.strip()
        if not title:
            raise TacheInvalideException("L’étape a besoin d’un titre.")
        if data.status not in STATUTS_ETAPE:
            raise TacheInvalideException("Ce statut d’étape n’existe pas.")
        await self._check_responsable(data.responsable_id)
        etape = await self._etapes.save(
            Etape(
                tache_id=tache.id,
                title=title,
                responsable_id=data.responsable_id,
                livrable=data.livrable.strip(),
                status=data.status,
                start_date=data.start_date,
                due_date=data.due_date,
                notes=data.notes.strip(),
                position=await self._etapes.max_position(tache.id) + 1,
                ref_externe=data.ref_externe,
            )
        )
        await self._touch(tache)
        if commit:
            await self._transaction.commit()
        return etape


class UpdateEtapeUseCase(_EtapeUseCase):
    async def __call__(self, actor: Membre, tache_id: int, etape_id: int, changes: ChangementsEtape) -> Etape:
        tache = await self._tache(tache_id)
        etape = await self._etape(tache_id, etape_id)
        f = changes.fields
        if "title" in f:
            title = (changes.title or "").strip()
            if not title:
                raise TacheInvalideException("L’étape a besoin d’un titre.")
            etape.title = title
        if "responsable_id" in f:
            await self._check_responsable(changes.responsable_id)
            etape.responsable_id = changes.responsable_id
        if "livrable" in f:
            etape.livrable = (changes.livrable or "").strip()
        if "status" in f:
            if changes.status not in STATUTS_ETAPE:
                raise TacheInvalideException("Ce statut d’étape n’existe pas.")
            etape.status = changes.status
        if "start_date" in f:
            etape.start_date = changes.start_date
        if "due_date" in f:
            etape.due_date = changes.due_date
        if "notes" in f:
            etape.notes = (changes.notes or "").strip()
        if "position" in f and changes.position is not None:
            etape.position = changes.position
        etape.updated_at = datetime.now(timezone.utc)
        etape = await self._etapes.save(etape)
        await self._touch(tache)
        await self._transaction.commit()
        return etape


class ArchiveEtapeUseCase(_EtapeUseCase):
    """Retire une étape de la tâche, sans l'effacer."""

    async def __call__(self, actor: Membre, tache_id: int, etape_id: int) -> Etape:
        tache = await self._tache(tache_id)
        etape = await self._etape(tache_id, etape_id)
        etape.archived = True
        etape.updated_at = datetime.now(timezone.utc)
        etape = await self._etapes.save(etape)
        await self._touch(tache)
        await self._transaction.commit()
        return etape
