from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Optional

# Les colonnes de la salle de projet.
A_FAIRE = "a_faire"
EN_COURS = "en_cours"
EN_ATTENTE = "en_attente"
FAIT = "fait"
STATUTS = (A_FAIRE, EN_COURS, EN_ATTENTE, FAIT)

# D'où vient une tâche : un humain, un agent, un retour de testeur, ou l'ancien tableau Google.
SOURCES = ("humain", "agent", "testflight", "tableau")

# Priorités, comme dans le tableau de pré-lancement : P0 bloque tout, P3 peut attendre.
PRIORITES = {"P0": "Critique", "P1": "Haute", "P2": "Moyenne", "P3": "Basse"}


@dataclass
class Tache:
    """Une tâche de la salle de projet. Humains et agents peuvent en recevoir, au même titre."""

    title: str
    created_by: int
    description: str = ""
    status: str = A_FAIRE
    assignee_id: Optional[int] = None
    pole: str = ""  # le pôle qui porte la tâche (Opérations, Produit, Croissance, Direction)
    due_date: Optional[date] = None
    priority: str = ""  # clé de PRIORITES, vide si non précisée
    objectif_id: Optional[int] = None  # l'objectif du trimestre qu'elle sert
    position: float = 0.0
    source: str = "humain"
    retour_id: Optional[int] = None
    ref_externe: Optional[str] = None  # repère de l'import (ex. « tableau:tache:4 ») pour ne jamais importer deux fois
    archived: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    done_at: Optional[datetime] = None
    id: Optional[int] = None
