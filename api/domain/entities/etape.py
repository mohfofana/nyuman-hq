from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Optional

# Une sous-étape avance en trois temps (la colonne « en attente » reste au niveau de la tâche).
STATUTS_ETAPE = ("a_faire", "en_cours", "fait")


@dataclass
class Etape:
    """Une sous-étape d'une tâche (« 4.1 Finalisation de l'offre »), avec son responsable et son livrable."""

    tache_id: int
    title: str
    responsable_id: Optional[int] = None
    livrable: str = ""
    status: str = "a_faire"
    start_date: Optional[date] = None
    due_date: Optional[date] = None
    notes: str = ""  # blocages, notes, preuves
    position: float = 0.0
    ref_externe: Optional[str] = None
    archived: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    id: Optional[int] = None
