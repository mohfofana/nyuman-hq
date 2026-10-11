from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import List, Optional

# Les statuts du tableau de pré-lancement, plus « refusé ».
STATUTS_DECISION = {
    "nouveau": "Sur la table",
    "a_initier": "À initier",
    "en_cours": "En cours",
    "valide": "Validé",
    "ajourne": "Ajourné",
    "refuse": "Refusé",
}
# Une fois tranché (oui ou non), le sujet entre au journal et sera revu à 30 jours : qui avait raison ?
TRANCHES = ("valide", "refuse")
REVUE_APRES = timedelta(days=30)

VOTES = ("pour", "contre", "abstention")
VERDICTS = {"bonne": "C’était la bonne décision", "mitigee": "Mitigé", "mauvaise": "Il fallait faire autrement"}


@dataclass
class Vote:
    decision_id: int
    membre_id: int
    vote: str
    commentaire: str = ""
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    id: Optional[int] = None


@dataclass
class Decision:
    """Un sujet de la salle du conseil : une demande, l'objectif servi, les risques, les votes des heads, la décision."""

    titre: str
    author_id: int
    demande: str = ""  # le sujet en détail, le contexte
    pole_concerne: str = ""
    poles_en_charge: List[str] = field(default_factory=list)
    objectif: str = ""  # quel objectif ça sert, avec quel chiffre
    risques: str = ""  # pourquoi ça pourrait échouer
    decision: str = ""  # ce qui a été acté
    liens: str = ""
    statut: str = "nouveau"
    date_demande: Optional[date] = None
    decided_at: Optional[datetime] = None
    decided_by: Optional[int] = None
    bilan: str = ""
    bilan_verdict: str = ""
    bilan_at: Optional[datetime] = None
    ref_externe: Optional[str] = None
    archived: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    id: Optional[int] = None

    def revue_due(self, now: datetime) -> Optional[datetime]:
        """Date de la revue à 30 jours, pour un sujet tranché qui n'a pas encore son bilan."""
        if self.statut not in TRANCHES or self.decided_at is None or self.bilan_verdict:
            return None
        return self.decided_at + REVUE_APRES

    def a_revoir(self, now: datetime) -> bool:
        due = self.revue_due(now)
        return due is not None and now >= due
