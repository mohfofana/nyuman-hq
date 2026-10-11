from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

# Ce que dit le retour.
BUG = "bug"
IDEE = "idee"
REMARQUE = "remarque"
KINDS = (BUG, IDEE, REMARQUE)

# D'où il vient : posté dans HQ par un membre de l'équipe, ou importé de TestFlight.
SOURCE_HQ = "hq"
SOURCE_TESTFLIGHT = "testflight"

# Côté de l'app concerné.
ESPACES = ("cliente", "pro", "")

NOUVEAU = "nouveau"
EN_TACHE = "en_tache"
CLASSE = "classe"


@dataclass
class Retour:
    """Un retour sur l'app Nyuman pendant les tests : un bug, une idée ou une remarque, avec ses captures."""

    kind: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    source: str = SOURCE_HQ
    comment: str = ""
    author_id: Optional[int] = None  # membre de l'équipe qui l'a posté (source HQ)
    tester_email: Optional[str] = None  # testeur TestFlight (source TestFlight)
    espace: str = ""
    device_model: str = ""
    os_version: str = ""
    build_version: str = ""
    captures: List[str] = field(default_factory=list)  # noms des images gardées par HQ
    statut: str = NOUVEAU
    tache_id: Optional[int] = None
    asc_id: Optional[str] = None  # identifiant App Store Connect, pour ne pas importer deux fois
    id: Optional[int] = None
