from datetime import date, datetime
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from adapters.core.membre.contract.membre_view_model import MemberRefViewModel
from domain.entities.etape import Etape
from domain.entities.membre import Membre
from domain.entities.tache import Tache
from use_cases.core.etape.etape_use_cases import ChangementsEtape, NouvelleEtape
from use_cases.core.tache.tache_use_cases import ChangementsTache, NouvelleTache

StatutLiteral = Literal["a_faire", "en_cours", "en_attente", "fait"]
PoleLiteral = Literal["direction", "operations", "produit", "croissance", ""]
PrioriteLiteral = Literal["P0", "P1", "P2", "P3", ""]
StatutEtapeLiteral = Literal["a_faire", "en_cours", "fait"]


class EtapeViewModel(BaseModel):
    id: int
    title: str
    responsable: Optional[MemberRefViewModel]
    livrable: str
    status: str
    start_date: Optional[date]
    due_date: Optional[date]
    notes: str
    position: float

    @classmethod
    def of(cls, etape: Etape, membres: Dict[int, Membre]) -> "EtapeViewModel":
        responsable = membres.get(etape.responsable_id) if etape.responsable_id else None
        return cls(
            id=etape.id,
            title=etape.title,
            responsable=MemberRefViewModel.of(responsable) if responsable else None,
            livrable=etape.livrable,
            status=etape.status,
            start_date=etape.start_date,
            due_date=etape.due_date,
            notes=etape.notes,
            position=etape.position,
        )


class TacheViewModel(BaseModel):
    id: int
    title: str
    description: str
    status: str
    assignee: Optional[MemberRefViewModel]
    pole: str
    due_date: Optional[date]
    priority: str
    objectif_id: Optional[int]
    position: float
    source: str
    retour_id: Optional[int]
    created_by: MemberRefViewModel
    created_at: datetime
    updated_at: datetime
    done_at: Optional[datetime]
    etapes: List[EtapeViewModel]

    @classmethod
    def of(cls, tache: Tache, membres: Dict[int, Membre], etapes: Optional[List[Etape]] = None) -> "TacheViewModel":
        assignee = membres.get(tache.assignee_id) if tache.assignee_id else None
        return cls(
            id=tache.id,
            title=tache.title,
            description=tache.description,
            status=tache.status,
            assignee=MemberRefViewModel.of(assignee) if assignee else None,
            pole=tache.pole,
            due_date=tache.due_date,
            priority=tache.priority,
            objectif_id=tache.objectif_id,
            position=tache.position,
            source=tache.source,
            retour_id=tache.retour_id,
            created_by=MemberRefViewModel.of(membres[tache.created_by]),
            created_at=tache.created_at,
            updated_at=tache.updated_at,
            done_at=tache.done_at,
            etapes=[EtapeViewModel.of(e, membres) for e in (etapes or [])],
        )


class CreateTacheRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=50_000)
    status: StatutLiteral = "a_faire"
    assignee_id: Optional[int] = None
    pole: PoleLiteral = ""
    due_date: Optional[date] = None
    priority: PrioriteLiteral = ""
    objectif: bool = True

    def to_input(self) -> NouvelleTache:
        return NouvelleTache(**self.model_dump())


class UpdateTacheRequest(BaseModel):
    title: Optional[str] = Field(default=None, max_length=200)
    description: Optional[str] = Field(default=None, max_length=50_000)
    status: Optional[StatutLiteral] = None
    assignee_id: Optional[int] = None
    pole: Optional[PoleLiteral] = None
    due_date: Optional[date] = None
    priority: Optional[PrioriteLiteral] = None
    position: Optional[float] = None
    objectif: Optional[bool] = None

    def to_changes(self) -> ChangementsTache:
        # On ne touche qu'aux champs envoyés : { "assignee_id": null } retire la personne, l'absence du champ ne change rien.
        return ChangementsTache(fields=set(self.model_fields_set), **self.model_dump())


class CreateEtapeRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    responsable_id: Optional[int] = None
    livrable: str = Field(default="", max_length=2000)
    status: StatutEtapeLiteral = "a_faire"
    start_date: Optional[date] = None
    due_date: Optional[date] = None
    notes: str = Field(default="", max_length=5000)

    def to_input(self) -> NouvelleEtape:
        return NouvelleEtape(**self.model_dump())


class UpdateEtapeRequest(BaseModel):
    title: Optional[str] = Field(default=None, max_length=200)
    responsable_id: Optional[int] = None
    livrable: Optional[str] = Field(default=None, max_length=2000)
    status: Optional[StatutEtapeLiteral] = None
    start_date: Optional[date] = None
    due_date: Optional[date] = None
    notes: Optional[str] = Field(default=None, max_length=5000)
    position: Optional[float] = None

    def to_changes(self) -> ChangementsEtape:
        return ChangementsEtape(fields=set(self.model_fields_set), **self.model_dump())
