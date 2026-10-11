from datetime import datetime, timezone

from domain.entities.evenement import Evenement
from domain.entities.membre import HUMAIN, Membre, initiales, nom_depuis_email
from use_cases.common.ports.out.google_token_verifier import GoogleTokenVerifier
from use_cases.common.ports.out.transaction import Transaction
from use_cases.core.evenement.repository.evenement_repository import EvenementRepository
from use_cases.core.membre.exceptions.membre_exceptions import AccesRefuseException
from use_cases.core.membre.repository.membre_repository import MembreRepository


class LoginWithGoogleUseCase:
    """Seules les adresses ajoutées par un head entrent. Le nom Google remplace le nom provisoire."""

    def __init__(
        self,
        verifier: GoogleTokenVerifier,
        membre_repository: MembreRepository,
        evenement_repository: EvenementRepository,
        transaction: Transaction,
    ):
        self._verifier = verifier
        self._membre_repository = membre_repository
        self._evenement_repository = evenement_repository
        self._transaction = transaction

    async def __call__(self, credential: str) -> Membre:
        identity = await self._verifier.verify(credential)
        membre = await self._membre_repository.find_by_email(identity.email)
        if membre is None or membre.kind != HUMAIN or not membre.active:
            raise AccesRefuseException()

        first_visit = membre.last_seen_at is None
        provisoire = membre.name in (membre.email, nom_depuis_email(membre.email or ""))
        if identity.name and provisoire:
            membre.name = identity.name
            membre.initials = initiales(identity.name)
        membre.last_seen_at = datetime.now(timezone.utc)
        membre = await self._membre_repository.save(membre)

        if first_visit:
            await self._evenement_repository.add(
                Evenement(actor_id=membre.id, verb="arrivee", text="est entré dans la maison pour la première fois.")
            )
        await self._transaction.commit()
        return membre
