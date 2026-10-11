from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel, Field

from adapters.core.membre.contract.membre_view_model import MemberRefViewModel
from domain.entities.membre import Membre
from domain.entities.retour import Retour


class RetourViewModel(BaseModel):
    id: int
    kind: str
    source: str
    comment: str
    author: Optional[MemberRefViewModel]
    tester_email: Optional[str]
    espace: str
    device_model: str
    os_version: str
    build_version: str
    captures: int  # nombre de captures ; chacune se lit sur /api/retours/{id}/captures/{n}
    statut: str
    tache_id: Optional[int]
    created_at: datetime

    @classmethod
    def of(cls, retour: Retour, membres: Dict[int, Membre]) -> "RetourViewModel":
        author = membres.get(retour.author_id) if retour.author_id else None
        return cls(
            id=retour.id,
            kind=retour.kind,
            source=retour.source,
            comment=retour.comment,
            author=MemberRefViewModel.of(author) if author else None,
            tester_email=retour.tester_email,
            espace=retour.espace,
            device_model=retour.device_model,
            os_version=retour.os_version,
            build_version=retour.build_version,
            captures=len(retour.captures),
            statut=retour.statut,
            tache_id=retour.tache_id,
            created_at=retour.created_at,
        )


class ConvertRetourRequest(BaseModel):
    title: Optional[str] = Field(default=None, max_length=200)
    assignee_id: Optional[int] = None


class RetoursEtatViewModel(BaseModel):
    nouveaux: int
    testflight_branche: bool
    derniere_synchro: Optional[datetime]
    derniere_erreur: Optional[str]
