from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional, Set

from domain.entities.evenement import Evenement
from domain.entities.membre import Membre
from domain.entities.pro import ACCES_TEST, CATEGORIES_PRO, CONTRATS, Pro
from use_cases.common.ports.out.transaction import Transaction
from use_cases.core.evenement.repository.evenement_repository import EvenementRepository
from use_cases.core.membre.repository.membre_repository import MembreRepository
from use_cases.core.pro.exceptions.pro_exceptions import ProInvalideException, ProNotFoundException
from use_cases.core.pro.repository.pro_repository import ProRepository

_TEXTES = ("nom", "enseigne", "audience", "telephone", "email", "notes")


def _link(pro: Pro) -> str:
    return f"/pros?fiche={pro.id}"


@dataclass
class NouveauPro:
    nom: str
    categorie: str = "partenaire"
    enseigne: str = ""
    audience: str = ""
    telephone: str = ""
    email: str = ""
    contrat: str = ""
    acces_test: str = ""
    notes: str = ""
    suivi_par_id: Optional[int] = None
    numero: Optional[int] = None
    ref_externe: Optional[str] = None


@dataclass
class ChangementsPro:
    fields: Set[str] = field(default_factory=set)
    nom: Optional[str] = None
    categorie: Optional[str] = None
    enseigne: Optional[str] = None
    audience: Optional[str] = None
    telephone: Optional[str] = None
    email: Optional[str] = None
    contrat: Optional[str] = None
    acces_test: Optional[str] = None
    notes: Optional[str] = None
    suivi_par_id: Optional[int] = None


class _ProUseCase:
    def __init__(
        self,
        pro_repository: ProRepository,
        membre_repository: MembreRepository,
        evenement_repository: EvenementRepository,
        transaction: Transaction,
    ):
        self._pros = pro_repository
        self._membres = membre_repository
        self._evenements = evenement_repository
        self._transaction = transaction

    async def _check(self, pro: Pro) -> None:
        if not pro.nom:
            raise ProInvalideException("La fiche a besoin d’un nom.")
        if pro.categorie not in CATEGORIES_PRO:
            raise ProInvalideException("Cette catégorie n’existe pas.")
        if pro.contrat not in CONTRATS:
            raise ProInvalideException("Ce statut de contrat n’existe pas.")
        if pro.acces_test not in ACCES_TEST:
            raise ProInvalideException("Ce statut d’accès aux tests n’existe pas.")
        if pro.email and ("@" not in pro.email or " " in pro.email):
            raise ProInvalideException("Cette adresse email n’est pas valable.")
        if pro.suivi_par_id is not None:
            membre = await self._membres.find_by_id(pro.suivi_par_id)
            if membre is None or not membre.active:
                raise ProInvalideException("Cette personne ne fait pas partie de la maison.")


class CreateProUseCase(_ProUseCase):
    async def __call__(self, actor: Membre, data: NouveauPro, commit: bool = True, announce: bool = True) -> Pro:
        pro = Pro(
            created_by=actor.id,
            categorie=data.categorie,
            contrat=data.contrat,
            acces_test=data.acces_test,
            suivi_par_id=data.suivi_par_id,
            numero=data.numero,
            ref_externe=data.ref_externe,
            **{name: (getattr(data, name) or "").strip() for name in _TEXTES},
        )
        pro.email = pro.email.lower()
        await self._check(pro)
        pro = await self._pros.save(pro)
        if announce:
            # Le fil ne montre jamais de téléphone ni d'email : seulement l'enseigne.
            await self._evenements.add(
                Evenement(actor_id=actor.id, verb="pro_ajoute", text=f"a ajouté « {pro.libelle} » au panel des pros.", link=_link(pro))
            )
        if commit:
            await self._transaction.commit()
        return pro


class UpdateProUseCase(_ProUseCase):
    async def __call__(self, actor: Membre, pro_id: int, changes: ChangementsPro) -> Pro:
        pro = await self._pros.find_by_id(pro_id)
        if pro is None or pro.archived:
            raise ProNotFoundException()
        before_acces = pro.acces_test
        f = changes.fields
        for name in _TEXTES:
            if name in f:
                setattr(pro, name, (getattr(changes, name) or "").strip())
        pro.email = pro.email.lower()
        for name in ("categorie", "contrat", "acces_test"):
            if name in f:
                setattr(pro, name, getattr(changes, name) or "")
        if "suivi_par_id" in f:
            pro.suivi_par_id = changes.suivi_par_id
        await self._check(pro)
        pro.updated_at = datetime.now(timezone.utc)
        pro = await self._pros.save(pro)
        if pro.acces_test != before_acces and pro.acces_test in ("envoye", "actif"):
            text = (
                f"a envoyé l’accès aux tests à « {pro.libelle} »."
                if pro.acces_test == "envoye"
                else f"a noté que « {pro.libelle} » teste l’app."
            )
            await self._evenements.add(Evenement(actor_id=actor.id, verb="pro_acces", text=text, link=_link(pro)))
        await self._transaction.commit()
        return pro


class ArchiveProUseCase(_ProUseCase):
    """Retire une fiche du panel sans l'effacer."""

    async def __call__(self, actor: Membre, pro_id: int) -> Pro:
        pro = await self._pros.find_by_id(pro_id)
        if pro is None or pro.archived:
            raise ProNotFoundException()
        pro.archived = True
        pro.updated_at = datetime.now(timezone.utc)
        pro = await self._pros.save(pro)
        await self._transaction.commit()
        return pro


class GetProListUseCase:
    def __init__(self, pro_repository: ProRepository):
        self._pros = pro_repository

    async def __call__(self) -> List[Pro]:
        return await self._pros.list_active()
