from datetime import date, datetime, timezone
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from adapters.core.membre.contract.membre_view_model import MemberRefViewModel
from domain.entities.decision import Decision, Vote
from domain.entities.membre import Membre
from use_cases.core.decision.decision_use_cases import ChangementsDecision, NouvelleDecision

StatutLiteral = Literal["nouveau", "a_initier", "en_cours", "valide", "ajourne", "refuse"]
PoleLiteral = Literal["direction", "operations", "produit", "croissance", ""]
PoleNonVideLiteral = Literal["direction", "operations", "produit", "croissance"]


class VoteViewModel(BaseModel):
    membre: MemberRefViewModel
    vote: str
    commentaire: str
    updated_at: datetime

    @classmethod
    def of(cls, vote: Vote, membres: Dict[int, Membre]) -> "VoteViewModel":
        return cls(
            membre=MemberRefViewModel.of(membres[vote.membre_id]),
            vote=vote.vote,
            commentaire=vote.commentaire,
            updated_at=vote.updated_at,
        )


class DecisionViewModel(BaseModel):
    id: int
    titre: str
    demande: str
    pole_concerne: str
    poles_en_charge: List[str]
    objectif: str
    risques: str
    decision: str
    liens: str
    statut: str
    date_demande: Optional[date]
    decided_at: Optional[datetime]
    decided_by: Optional[MemberRefViewModel]
    revue_le: Optional[datetime]
    a_revoir: bool
    bilan: str
    bilan_verdict: str
    bilan_at: Optional[datetime]
    author: MemberRefViewModel
    votes: List[VoteViewModel]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def of(cls, decision: Decision, membres: Dict[int, Membre], votes: Optional[List[Vote]] = None) -> "DecisionViewModel":
        now = datetime.now(timezone.utc)
        decided_by = membres.get(decision.decided_by) if decision.decided_by else None
        return cls(
            id=decision.id,
            titre=decision.titre,
            demande=decision.demande,
            pole_concerne=decision.pole_concerne,
            poles_en_charge=decision.poles_en_charge,
            objectif=decision.objectif,
            risques=decision.risques,
            decision=decision.decision,
            liens=decision.liens,
            statut=decision.statut,
            date_demande=decision.date_demande,
            decided_at=decision.decided_at,
            decided_by=MemberRefViewModel.of(decided_by) if decided_by else None,
            revue_le=decision.revue_due(now),
            a_revoir=decision.a_revoir(now),
            bilan=decision.bilan,
            bilan_verdict=decision.bilan_verdict,
            bilan_at=decision.bilan_at,
            author=MemberRefViewModel.of(membres[decision.author_id]),
            votes=[VoteViewModel.of(v, membres) for v in (votes or []) if v.membre_id in membres],
            created_at=decision.created_at,
            updated_at=decision.updated_at,
        )


class CreateDecisionRequest(BaseModel):
    titre: str = Field(min_length=1, max_length=200)
    demande: str = Field(default="", max_length=20_000)
    pole_concerne: PoleLiteral = ""
    poles_en_charge: List[PoleNonVideLiteral] = Field(default_factory=list, max_length=4)
    objectif: str = Field(default="", max_length=5000)
    risques: str = Field(default="", max_length=5000)
    liens: str = Field(default="", max_length=5000)

    def to_input(self) -> NouvelleDecision:
        return NouvelleDecision(**self.model_dump())


class UpdateDecisionRequest(BaseModel):
    titre: Optional[str] = Field(default=None, max_length=200)
    demande: Optional[str] = Field(default=None, max_length=20_000)
    pole_concerne: Optional[PoleLiteral] = None
    poles_en_charge: Optional[List[PoleNonVideLiteral]] = Field(default=None, max_length=4)
    objectif: Optional[str] = Field(default=None, max_length=5000)
    risques: Optional[str] = Field(default=None, max_length=5000)
    decision: Optional[str] = Field(default=None, max_length=20_000)
    liens: Optional[str] = Field(default=None, max_length=5000)
    statut: Optional[StatutLiteral] = None
    date_demande: Optional[date] = None

    def to_changes(self) -> ChangementsDecision:
        return ChangementsDecision(fields=set(self.model_fields_set), **self.model_dump())


class VoteRequest(BaseModel):
    vote: Literal["pour", "contre", "abstention"]
    commentaire: str = Field(default="", max_length=2000)


class BilanRequest(BaseModel):
    verdict: Literal["bonne", "mitigee", "mauvaise"]
    bilan: str = Field(default="", max_length=10_000)
