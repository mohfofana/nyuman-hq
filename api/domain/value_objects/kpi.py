from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

# Les KPI viennent de la route statistiques de nyuman-api : des totaux seulement, aucune donnée personnelle.
KPI_DEFINITIONS = [
    ("utilisateurs_inscrits", "Utilisateurs inscrits", "nombre"),
    ("pros_actifs", "Pros actifs (30 jours)", "nombre"),
    ("reservations_7j", "Réservations payées (7 jours)", "nombre"),
    ("acomptes_7j_fcfa", "Acomptes encaissés (7 jours)", "fcfa"),
    ("revenu_nyuman_7j_fcfa", "Revenu Nyuman (7 jours)", "fcfa"),
]

KPI_KEYS = [k for k, _, _ in KPI_DEFINITIONS]


@dataclass
class Kpi:
    key: str
    label: str
    value: float
    unit: str


@dataclass
class KpiSnapshot:
    available: bool
    reason: Optional[str] = None
    updated_at: Optional[datetime] = None
    values: List[Kpi] = field(default_factory=list)

    @classmethod
    def from_totals(cls, totals: Dict[str, float], updated_at: datetime) -> "KpiSnapshot":
        values = [Kpi(key, label, float(totals[key]), unit) for key, label, unit in KPI_DEFINITIONS if key in totals]
        return cls(available=True, updated_at=updated_at, values=values)

    @classmethod
    def unavailable(cls, reason: str) -> "KpiSnapshot":
        return cls(available=False, reason=reason)

    def value_of(self, key: str) -> Optional[float]:
        if not self.available:
            return None
        return next((k.value for k in self.values if k.key == key), None)
