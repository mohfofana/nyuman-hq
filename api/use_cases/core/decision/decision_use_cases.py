from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Dict, List, Optional, Set, Tuple

from domain.entities.decision import STATUTS_DECISION, TRANCHES, VERDICTS, VOTES, Decision, Vote
from domain.entities.evenement import Evenement
from domain.entities.membre import POLES, Membre
from use_cases.common.ports.out.transaction import Transaction
from use_cases.core.decision.exceptions.decision_exceptions import (
    DecisionInterditeException,
    DecisionInvalideException,
    DecisionNotFoundException,
)
from use_cases.core.decision.repository.decision_repository import DecisionRepository
from use_cases.core.evenement.repository.evenement_repository import EvenementRepository


def _link(decision: Decision) -> str:
    return f"/conseil?sujet={decision.id}"


def _check_poles(concerne: str, en_charge: List[str]) -> None:
    for pole in [concerne, *en_charge]:
        if pole and pole not in POLES:
            raise DecisionInvalideException("Ce pôle n’existe pas.")


@dataclass
class NouvelleDecision:
    titre: str
    demande: str = ""
    pole_concerne: str = ""
    poles_en_charge: List[str] = field(default_factory=list)
    objectif: str = ""
    risques: str = ""
    decision: str = ""
    liens: str = ""
    statut: str = "nouveau"
    date_demande: Optional[date] = None
    ref_externe: Optional[str] = None


@dataclass
class ChangementsDecision:
    fields: Set[str] = field(default_factory=set)
    titre: Optional[str] = None
    demande: Optional[str] = None
    pole_concerne: Optional[str] = None
    poles_en_charge: Optional[List[str]] = None
    objectif: Optional[str] = None
    risques: Optional[str] = None
    decision: Optional[str] = None
    liens: Optional[str] = None
    statut: Optional[str] = None
    date_demande: Optional[date] = None


class _DecisionUseCase:
    def __init__(self, decision_repository: DecisionRepository, evenement_repository: EvenementRepository, transaction: Transaction):
        self._decisions = decision_repository
        self._evenements = evenement_repository
        self._transaction = transaction

    async def _get(self, decision_id: int) -> Decision:
        decision = await self._decisions.find_by_id(decision_id)
        if decision is None or decision.archived:
            raise DecisionNotFoundException()
        return decision

    def _apply_statut(self, decision: Decision, statut: str, actor: Membre, now: datetime) -> None:
        if statut not in STATUTS_DECISION:
            raise DecisionInvalideException("Ce statut n’existe pas.")
        if statut in TRANCHES and decision.statut not in TRANCHES:
            decision.decided_at, decision.decided_by = now, actor.id
        elif statut not in TRANCHES:
            decision.decided_at, decision.decided_by = None, None
        decision.statut = statut


class CreateDecisionUseCase(_DecisionUseCase):
    """Tout humain de la maison peut mettre un sujet au conseil. Seuls les heads le tranchent."""

    async def __call__(self, actor: Membre, data: NouvelleDecision, commit: bool = True, announce: bool = True) -> Decision:
        titre = data.titre.strip()
        if not titre:
            raise DecisionInvalideException("Le sujet a besoin d’un titre.")
        _check_poles(data.pole_concerne, data.poles_en_charge)
        if data.statut != "nouveau" and not actor.is_head:
            raise DecisionInterditeException("Seul un head peut trancher un sujet.")
        now = datetime.now(timezone.utc)
        decision = Decision(
            titre=titre,
            author_id=actor.id,
            demande=data.demande.strip(),
            pole_concerne=data.pole_concerne,
            poles_en_charge=list(dict.fromkeys(data.poles_en_charge)),
            objectif=data.objectif.strip(),
            risques=data.risques.strip(),
            decision=data.decision.strip(),
            liens=data.liens.strip(),
            date_demande=data.date_demande or now.date(),
            ref_externe=data.ref_externe,
        )
        self._apply_statut(decision, data.statut, actor, now)
        if decision.decided_at and data.date_demande:
            # Sujet repris d'un historique : il a été tranché le jour de la demande, pas aujourd'hui.
            decision.decided_at = datetime.combine(data.date_demande, datetime.min.time(), tzinfo=timezone.utc)
        decision = await self._decisions.save(decision)
        if announce:
            await self._evenements.add(
                Evenement(actor_id=actor.id, verb="conseil_sujet", text=f"a mis au conseil : « {decision.titre} ».", link=_link(decision))
            )
        if commit:
            await self._transaction.commit()
        return decision


class UpdateDecisionUseCase(_DecisionUseCase):
    async def __call__(self, actor: Membre, decision_id: int, changes: ChangementsDecision) -> Decision:
        decision = await self._get(decision_id)
        f = changes.fields
        if not actor.is_head and actor.id != decision.author_id:
            raise DecisionInterditeException("Seuls l’auteur du sujet et les heads peuvent le modifier.")
        if ("statut" in f or "decision" in f) and not actor.is_head:
            raise DecisionInterditeException("Seul un head peut trancher un sujet.")

        if "titre" in f:
            titre = (changes.titre or "").strip()
            if not titre:
                raise DecisionInvalideException("Le sujet a besoin d’un titre.")
            decision.titre = titre
        for name in ("demande", "objectif", "risques", "decision", "liens"):
            if name in f:
                setattr(decision, name, (getattr(changes, name) or "").strip())
        if "pole_concerne" in f or "poles_en_charge" in f:
            concerne = changes.pole_concerne if "pole_concerne" in f else decision.pole_concerne
            en_charge = changes.poles_en_charge if "poles_en_charge" in f else decision.poles_en_charge
            _check_poles(concerne or "", en_charge or [])
            decision.pole_concerne = concerne or ""
            decision.poles_en_charge = list(dict.fromkeys(en_charge or []))
        if "date_demande" in f and changes.date_demande:
            decision.date_demande = changes.date_demande

        before = decision.statut
        now = datetime.now(timezone.utc)
        if "statut" in f and changes.statut != before:
            self._apply_statut(decision, changes.statut or "", actor, now)
        decision.updated_at = now
        decision = await self._decisions.save(decision)

        if decision.statut != before:
            textes = {
                "valide": f"a tranché : oui à « {decision.titre} ».",
                "refuse": f"a tranché : non à « {decision.titre} ».",
                "ajourne": f"a ajourné « {decision.titre} ».",
            }
            text = textes.get(decision.statut)
            if text:
                await self._evenements.add(Evenement(actor_id=actor.id, verb="conseil_decision", text=text, link=_link(decision)))
        await self._transaction.commit()
        return decision


class VoteDecisionUseCase(_DecisionUseCase):
    """Les heads votent tant que le sujet est sur la table. Un nouveau vote remplace l'ancien."""

    async def __call__(self, actor: Membre, decision_id: int, vote: str, commentaire: str = "") -> Vote:
        decision = await self._get(decision_id)
        if not actor.is_head:
            raise DecisionInterditeException("Seuls les heads votent au conseil.")
        if vote not in VOTES:
            raise DecisionInvalideException("Vote possible : pour, contre ou abstention.")
        if decision.statut in TRANCHES:
            raise DecisionInvalideException("Ce sujet est déjà tranché.")
        existing = await self._decisions.find_vote(decision.id, actor.id)
        saved = await self._decisions.save_vote(
            Vote(
                id=existing.id if existing else None,
                decision_id=decision.id,
                membre_id=actor.id,
                vote=vote,
                commentaire=commentaire.strip(),
            )
        )
        await self._transaction.commit()
        return saved


class BilanDecisionUseCase(_DecisionUseCase):
    """La revue à 30 jours : avec le recul, était-ce la bonne décision ?"""

    async def __call__(self, actor: Membre, decision_id: int, verdict: str, bilan: str) -> Decision:
        decision = await self._get(decision_id)
        if not actor.is_head:
            raise DecisionInterditeException("Seul un head peut faire le bilan d’une décision.")
        if decision.statut not in TRANCHES:
            raise DecisionInvalideException("On fait le bilan d’un sujet une fois qu’il est tranché.")
        if verdict not in VERDICTS:
            raise DecisionInvalideException("Ce verdict n’existe pas.")
        now = datetime.now(timezone.utc)
        decision.bilan_verdict, decision.bilan, decision.bilan_at = verdict, bilan.strip(), now
        decision.updated_at = now
        decision = await self._decisions.save(decision)
        await self._evenements.add(
            Evenement(
                actor_id=actor.id,
                verb="conseil_bilan",
                text=f"a fait le bilan de « {decision.titre} » : {VERDICTS[verdict].lower()}.",
                link=_link(decision),
            )
        )
        await self._transaction.commit()
        return decision


class ArchiveDecisionUseCase(_DecisionUseCase):
    async def __call__(self, actor: Membre, decision_id: int) -> Decision:
        decision = await self._get(decision_id)
        if not actor.is_head and actor.id != decision.author_id:
            raise DecisionInterditeException("Seuls l’auteur du sujet et les heads peuvent le retirer.")
        decision.archived = True
        decision.updated_at = datetime.now(timezone.utc)
        decision = await self._decisions.save(decision)
        await self._transaction.commit()
        return decision


class GetConseilUseCase:
    """Tous les sujets du conseil, avec les votes de chacun."""

    def __init__(self, decision_repository: DecisionRepository):
        self._decisions = decision_repository

    async def __call__(self) -> Tuple[List[Decision], Dict[int, List[Vote]]]:
        decisions = await self._decisions.list_active()
        votes = await self._decisions.votes_for([d.id for d in decisions])
        return decisions, votes
