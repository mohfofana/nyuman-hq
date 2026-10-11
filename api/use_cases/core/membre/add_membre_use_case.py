from domain.entities.evenement import Evenement
from domain.entities.membre import COULEURS_HUMAINS, HEAD, HUMAIN, MEMBRE, POLES, Membre
from use_cases.common.ports.out.transaction import Transaction
from use_cases.core.evenement.repository.evenement_repository import EvenementRepository
from use_cases.core.membre.exceptions.membre_exceptions import (
    MembreDejaPresentException,
    ModificationInterditeException,
    ReserveAuxHeadsException,
)
from use_cases.core.membre.repository.membre_repository import MembreRepository


class AddMembreUseCase:
    """Un head fait entrer un humain dans la maison : son adresse Google peut alors se connecter."""

    def __init__(
        self,
        membre_repository: MembreRepository,
        evenement_repository: EvenementRepository,
        transaction: Transaction,
    ):
        self._membre_repository = membre_repository
        self._evenement_repository = evenement_repository
        self._transaction = transaction

    async def __call__(self, actor: Membre, email: str, name: str, title: str, role: str, pole: str = "") -> Membre:
        if not actor.is_head:
            raise ReserveAuxHeadsException()
        if role not in (HEAD, MEMBRE):
            raise ModificationInterditeException("Les droits possibles sont « head » ou « membre ».")
        if pole and pole not in POLES:
            raise ModificationInterditeException("Ce pôle n’existe pas.")
        email = email.strip().lower()
        if await self._membre_repository.find_by_email(email):
            raise MembreDejaPresentException()

        count = await self._membre_repository.count_humans()
        membre = await self._membre_repository.save(
            Membre(
                name=name.strip(),
                email=email,
                title=title.strip(),
                role=role,
                pole=pole,
                kind=HUMAIN,
                color=COULEURS_HUMAINS[count % len(COULEURS_HUMAINS)],
            )
        )
        await self._evenement_repository.add(
            Evenement(actor_id=actor.id, verb="membre_ajoute", text=f"a fait entrer {membre.name} dans la maison.")
        )
        await self._transaction.commit()
        return membre
