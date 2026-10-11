from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Optional


def semaine_iso(jour: date) -> str:
    """« 2026-W42 » : la semaine du rapport, du lundi au dimanche."""
    year, week, _ = jour.isocalendar()
    return f"{year}-W{week:02d}"


@dataclass
class Rapport:
    """Le rapport de la semaine d'un membre (humain ou, plus tard, agent) : fait, en cours, bloqué, 3 propositions."""

    author_id: int
    week: str
    pole: str = ""
    fait: str = ""
    en_cours: str = ""
    bloque: str = ""
    propositions: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    id: Optional[int] = None
