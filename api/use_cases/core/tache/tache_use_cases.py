from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import List, Optional, Set

from domain.entities.evenement import Evenement
from domain.entities.membre import POLES, Membre
from domain.entities.tache import FAIT, PRIORITES, SOURCES, STATUTS, Tache
from use_cases.common.ports.out.transaction import Transaction
from use_cases.core.evenement.repository.evenement_repository import EvenementRepository
from use_cases.core.membre.repository.membre_repository import MembreRepository
from use_cases.core.objectif.repository.objectif_repository import ObjectifRepository
from use_cases.core.tache.exceptions.tache_exceptions import TacheInvalideException, TacheNotFoundException
from use_cases.core.tache.repository.tache_repository import TacheRepository


def _link(tache: Tache) -> str:
    return f"/projet?tache={tache.id}"


async def _check_assignee(membres: MembreRepository, assignee_id: Optional[int]) -> Optional[Membre]:
    if assignee_id is None:
        return None
    membre = await membres.find_by_id(assignee_id)
    if membre is None or not membre.active:
        raise TacheInvalideException("Cette personne ne fait pas partie de la maison.")
    return membre


@dataclass
class NouvelleTache:
    title: str
    description: str = ""
    status: str = "a_faire"
    assignee_id: Optional[int] = None
    pole: str = ""  # vide : le pôle de la personne à qui elle est confiée
    due_date: Optional[date] = None
    priority: str = ""
    objectif: bool = True  # rattachée à l'objectif du trimestre, sauf avis contraire
    source: str = "humain"
    retour_id: Optional[int] = None
    ref_externe: Optional[str] = None


@dataclass
class ChangementsTache:
    """Seuls les champs listés dans `fields` sont modifiés (on peut ainsi retirer une personne ou une date)."""

    fields: Set[str] = field(default_factory=set)
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    assignee_id: Optional[int] = None
    pole: Optional[str] = None
    due_date: Optional[date] = None
    priority: Optional[str] = None
    position: Optional[float] = None
    objectif: Optional[bool] = None


def _check_priority(priority: Optional[str]) -> str:
    if priority and priority not in PRIORITES:
        raise TacheInvalideException("Cette priorité n’existe pas (P0 à P3).")
    return priority or ""


class _TacheUseCase:
    def __init__(
        self,
        tache_repository: TacheRepository,
        membre_repository: MembreRepository,
        objectif_repository: ObjectifRepository,
        evenement_repository: EvenementRepository,
        transaction: Transaction,
    ):
        self._taches = tache_repository
        self._membres = membre_repository
        self._objectifs = objectif_repository
        self._evenements = evenement_repository
        self._transaction = transaction

    async def _current_objectif_id(self) -> Optional[int]:
        objectif = await self._objectifs.find_latest()
        return objectif.id if objectif else None


class CreateTacheUseCase(_TacheUseCase):
    async def __call__(self, actor: Membre, data: NouvelleTache, commit: bool = True, announce: bool = True) -> Tache:
        title = data.title.strip()
        if not title:
            raise TacheInvalideException("La tâche a besoin d’un titre.")
        if data.status not in STATUTS:
            raise TacheInvalideException("Cette colonne n’existe pas.")
        if data.source not in SOURCES:
            raise TacheInvalideException("Cette origine n’existe pas.")
        if data.pole and data.pole not in POLES:
            raise TacheInvalideException("Ce pôle n’existe pas.")
        assignee = await _check_assignee(self._membres, data.assignee_id)
        priority = _check_priority(data.priority)

        tache = await self._taches.save(
            Tache(
                title=title,
                description=data.description,
                status=data.status,
                assignee_id=data.assignee_id,
                pole=data.pole or (assignee.pole if assignee else ""),
                due_date=data.due_date,
                priority=priority,
                objectif_id=await self._current_objectif_id() if data.objectif else None,
                position=await self._taches.max_position(data.status) + 1,
                source=data.source,
                retour_id=data.retour_id,
                ref_externe=data.ref_externe,
                created_by=actor.id,
                done_at=datetime.now(timezone.utc) if data.status == FAIT else None,
            )
        )
        if announce:
            text = f"a créé la tâche « {tache.title} »"
            if assignee and assignee.id != actor.id:
                text += f" et l’a confiée à {assignee.name}"
            await self._evenements.add(Evenement(actor_id=actor.id, verb="tache_creee", text=text + ".", link=_link(tache)))
        if commit:
            await self._transaction.commit()
        return tache


class UpdateTacheUseCase(_TacheUseCase):
    async def __call__(self, actor: Membre, tache_id: int, changes: ChangementsTache) -> Tache:
        tache = await self._taches.find_by_id(tache_id)
        if tache is None or tache.archived:
            raise TacheNotFoundException()
        f = changes.fields
        before_status, before_assignee = tache.status, tache.assignee_id

        if "title" in f:
            title = (changes.title or "").strip()
            if not title:
                raise TacheInvalideException("La tâche a besoin d’un titre.")
            tache.title = title
        if "description" in f:
            tache.description = changes.description or ""
        if "status" in f:
            if changes.status not in STATUTS:
                raise TacheInvalideException("Cette colonne n’existe pas.")
            tache.status = changes.status
            tache.done_at = (tache.done_at or datetime.now(timezone.utc)) if tache.status == FAIT else None
        if "assignee_id" in f:
            assignee = await _check_assignee(self._membres, changes.assignee_id)
            tache.assignee_id = changes.assignee_id
            if assignee and not tache.pole and "pole" not in f:
                tache.pole = assignee.pole
        if "pole" in f:
            if changes.pole and changes.pole not in POLES:
                raise TacheInvalideException("Ce pôle n’existe pas.")
            tache.pole = changes.pole or ""
        if "due_date" in f:
            tache.due_date = changes.due_date
        if "priority" in f:
            tache.priority = _check_priority(changes.priority)
        if "position" in f and changes.position is not None:
            tache.position = changes.position
        if "objectif" in f:
            tache.objectif_id = await self._current_objectif_id() if changes.objectif else None
        tache.updated_at = datetime.now(timezone.utc)
        tache = await self._taches.save(tache)

        # Le fil ne garde que ce qui compte : une tâche confiée, une tâche terminée.
        if tache.assignee_id != before_assignee and tache.assignee_id is not None:
            if tache.assignee_id == actor.id:
                text = f"a pris la tâche « {tache.title} »."
            else:
                assignee = await self._membres.find_by_id(tache.assignee_id)
                text = f"a confié la tâche « {tache.title} » à {assignee.name}."
            await self._evenements.add(Evenement(actor_id=actor.id, verb="tache_confiee", text=text, link=_link(tache)))
        if tache.status == FAIT and before_status != FAIT:
            await self._evenements.add(
                Evenement(actor_id=actor.id, verb="tache_faite", text=f"a terminé la tâche « {tache.title} ».", link=_link(tache))
            )
        await self._transaction.commit()
        return tache


class ArchiveTacheUseCase(_TacheUseCase):
    """Met une tâche à la corbeille : elle quitte le tableau mais n'est jamais effacée."""

    async def __call__(self, actor: Membre, tache_id: int) -> Tache:
        tache = await self._taches.find_by_id(tache_id)
        if tache is None:
            raise TacheNotFoundException()
        tache.archived = True
        tache.updated_at = datetime.now(timezone.utc)
        tache = await self._taches.save(tache)
        await self._transaction.commit()
        return tache


class GetTacheListUseCase:
    def __init__(self, tache_repository: TacheRepository):
        self._taches = tache_repository

    async def __call__(self, assignee_id: Optional[int] = None, archived: bool = False) -> List[Tache]:
        return await self._taches.search(assignee_id, archived)
