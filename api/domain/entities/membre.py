from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional

# Un membre de la maison : un humain ou un agent. Les deux ont les mêmes attributs, au même niveau.
HUMAIN = "humain"
AGENT = "agent"

HEAD = "head"
MEMBRE = "membre"

PRESENCE_EN_LIGNE = timedelta(minutes=5)

STATUS_LABELS = {
    "en_ligne": "En ligne",
    "travaille": "Travaille",
    "en_attente": "En attente",
    "bloque": "Bloqué",
    "absent": "Pas connecté",
    "en_preparation": "En préparation",
}

COULEURS_HUMAINS = ["orange", "gris", "ambre", "bleu", "vert", "rouge"]

# L'organisation de Nyuman : le CEO, et trois heads qui dirigent chacun un pôle et lui rendent compte.
POLES = {
    "direction": "Direction",
    "operations": "Opérations",
    "produit": "Produit",
    "croissance": "Croissance et marketing",
}

_MOTS_VIDES = {"de", "du", "des", "la", "le", "les", "et", "d", "l"}


def nom_depuis_email(email: str) -> str:
    """Nom provisoire, en attendant le vrai nom Google : « mohamed.fofana@nyuman.app » → « Mohamed Fofana »."""
    local = email.split("@")[0]
    parts = [p for p in local.replace("_", ".").replace("-", ".").split(".") if p]
    return " ".join(p.capitalize() for p in parts) or email


def initiales(name: str) -> str:
    """« Chris-Sullyvan Koffi » → « CK », « Kevin » → « K », « Chef de cabinet » → « CC »."""
    mots = [m for m in name.replace("-", " ").replace("'", " ").split() if m.lower() not in _MOTS_VIDES]
    if not mots:
        return "?"
    if len(mots) == 1:
        return mots[0][0].upper()
    return (mots[0][0] + mots[-1][0]).upper()


@dataclass
class Membre:
    name: str
    kind: str = HUMAIN
    role: str = MEMBRE
    email: Optional[str] = None
    title: str = ""
    pole: str = ""  # clé de POLES ; vide pour un agent transversal (le Contradicteur relit tout le monde)
    initials: str = ""
    color: str = "gris"
    status: str = "absent"
    active: bool = True
    last_seen_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    id: Optional[int] = None

    def __post_init__(self) -> None:
        if not self.initials:
            self.initials = initiales(self.name)

    @property
    def is_head(self) -> bool:
        return self.kind == HUMAIN and self.role == HEAD

    def current_status(self, now: datetime) -> str:
        # Un humain est « en ligne » s'il a utilisé HQ ces 5 dernières minutes. Un agent garde son statut de travail.
        if self.kind == AGENT:
            return self.status
        if self.last_seen_at and now - self.last_seen_at <= PRESENCE_EN_LIGNE:
            return "en_ligne"
        return "absent"
