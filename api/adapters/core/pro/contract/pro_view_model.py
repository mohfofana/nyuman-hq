from datetime import datetime
from typing import Dict, Literal, Optional

from pydantic import BaseModel, Field

from adapters.core.membre.contract.membre_view_model import MemberRefViewModel
from domain.entities.membre import Membre
from domain.entities.pro import Pro
from use_cases.core.pro.pro_use_cases import ChangementsPro, NouveauPro

CategorieLiteral = Literal["fondateur", "ambassadeur", "partenaire", "prospect"]
ContratLiteral = Literal["", "a_envoyer", "en_attente", "signe", "non_requis"]
AccesLiteral = Literal["", "a_envoyer", "envoye", "installe", "actif"]


class ProViewModel(BaseModel):
    id: int
    numero: Optional[int]
    categorie: str
    nom: str
    enseigne: str
    audience: str
    telephone: str
    email: str
    contrat: str
    acces_test: str
    notes: str
    suivi_par: Optional[MemberRefViewModel]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def of(cls, pro: Pro, membres: Dict[int, Membre]) -> "ProViewModel":
        suivi = membres.get(pro.suivi_par_id) if pro.suivi_par_id else None
        return cls(
            id=pro.id,
            numero=pro.numero,
            categorie=pro.categorie,
            nom=pro.nom,
            enseigne=pro.enseigne,
            audience=pro.audience,
            telephone=pro.telephone,
            email=pro.email,
            contrat=pro.contrat,
            acces_test=pro.acces_test,
            notes=pro.notes,
            suivi_par=MemberRefViewModel.of(suivi) if suivi else None,
            created_at=pro.created_at,
            updated_at=pro.updated_at,
        )


class CreateProRequest(BaseModel):
    nom: str = Field(min_length=1, max_length=120)
    categorie: CategorieLiteral = "partenaire"
    enseigne: str = Field(default="", max_length=120)
    audience: str = Field(default="", max_length=40)
    telephone: str = Field(default="", max_length=40)
    email: str = Field(default="", max_length=254)
    contrat: ContratLiteral = ""
    acces_test: AccesLiteral = ""
    notes: str = Field(default="", max_length=5000)
    suivi_par_id: Optional[int] = None

    def to_input(self) -> NouveauPro:
        return NouveauPro(**self.model_dump())


class UpdateProRequest(BaseModel):
    nom: Optional[str] = Field(default=None, max_length=120)
    categorie: Optional[CategorieLiteral] = None
    enseigne: Optional[str] = Field(default=None, max_length=120)
    audience: Optional[str] = Field(default=None, max_length=40)
    telephone: Optional[str] = Field(default=None, max_length=40)
    email: Optional[str] = Field(default=None, max_length=254)
    contrat: Optional[ContratLiteral] = None
    acces_test: Optional[AccesLiteral] = None
    notes: Optional[str] = Field(default=None, max_length=5000)
    suivi_par_id: Optional[int] = None

    def to_changes(self) -> ChangementsPro:
        return ChangementsPro(fields=set(self.model_fields_set), **self.model_dump())
