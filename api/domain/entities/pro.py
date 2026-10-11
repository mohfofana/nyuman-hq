from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

# Le panel des pros (salons, coiffeuses, barbiers) avec qui Nyuman démarre : fondateurs, partenaires, ambassadeurs.
CATEGORIES_PRO = {
    "fondateur": "Fondateur",
    "ambassadeur": "Ambassadeur",
    "partenaire": "Partenaire",
    "prospect": "Prospect",
}
CONTRATS = {"": "Pas renseigné", "a_envoyer": "À envoyer", "en_attente": "En attente", "signe": "Signé", "non_requis": "Pas nécessaire"}
ACCES_TEST = {"": "Pas renseigné", "a_envoyer": "Lien à envoyer", "envoye": "Lien envoyé", "installe": "App installée", "actif": "Teste l’app"}


@dataclass
class Pro:
    """Une fiche du panel. Données personnelles : visibles par l'équipe connectée seulement, jamais dans le fil."""

    nom: str
    created_by: int
    categorie: str = "partenaire"
    enseigne: str = ""  # nom du salon ou nom d'utilisateur sur les réseaux
    audience: str = ""  # tranche d'abonnés, ex. « 10K - 30K »
    telephone: str = ""
    email: str = ""  # adresse pour l'accès aux tests
    contrat: str = ""
    acces_test: str = ""
    notes: str = ""
    suivi_par_id: Optional[int] = None
    numero: Optional[int] = None  # numéro dans le panel
    ref_externe: Optional[str] = None
    archived: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    id: Optional[int] = None

    @property
    def libelle(self) -> str:
        """Ce qu'on montre dans le fil : l'enseigne si elle existe, sinon le nom."""
        return self.enseigne or self.nom
