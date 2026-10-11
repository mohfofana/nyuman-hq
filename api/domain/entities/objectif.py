import math
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Optional

# Un objectif peut suivre un chiffre de l'app (pros actifs…) ou un chiffre tenu à la main par le pôle
# (« 0 bug bloquant », « 1 000 abonnés TikTok »…).
METRIC_MANUEL = "manuel"


@dataclass
class SuiviObjectif:
    """Les chiffres déjà calculés par le serveur : l'écran n'a qu'à les afficher."""

    current: Optional[float]
    progress: Optional[float]
    weeks_left: int
    needed_per_week: Optional[float]


@dataclass
class Objectif:
    """L'objectif chiffré du trimestre : celui de toute la maison (pôle vide) ou celui d'un pôle."""

    title: str
    quarter: str
    metric: str
    target: float
    start_date: date
    end_date: date
    created_by: int
    pole: str = ""
    current_manual: Optional[float] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    id: Optional[int] = None

    @property
    def is_manual(self) -> bool:
        return self.metric == METRIC_MANUEL

    def suivi(self, current: Optional[float], today: date) -> SuiviObjectif:
        days_left = max(0, (self.end_date - today).days)
        weeks_left = math.ceil(days_left / 7)
        if current is None:
            return SuiviObjectif(current=None, progress=None, weeks_left=weeks_left, needed_per_week=None)
        progress = current / self.target if self.target else None
        remaining = max(0.0, self.target - current)
        needed = round(remaining / max(days_left / 7, 1), 1) if remaining else 0.0
        return SuiviObjectif(current=current, progress=progress, weeks_left=weeks_left, needed_per_week=needed)
