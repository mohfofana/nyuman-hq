from datetime import datetime, timezone

from domain.entities.membre import HUMAIN, Membre
from use_cases.common.ports.out.transaction import Transaction
from use_cases.core.membre.exceptions.membre_exceptions import AccesRefuseException
from use_cases.core.membre.repository.membre_repository import MembreRepository


class LoginDevUseCase:
    """Connexion sans Google, pour le développement local. Le contrôleur la refuse si elle n'est pas activée."""

    def __init__(self, membre_repository: MembreRepository, transaction: Transaction):
        self._membre_repository = membre_repository
        self._transaction = transaction

    async def __call__(self, email: str) -> Membre:
        membre = await self._membre_repository.find_by_email(email.strip().lower())
        if membre is None or membre.kind != HUMAIN or not membre.active:
            raise AccesRefuseException()
        membre.last_seen_at = datetime.now(timezone.utc)
        membre = await self._membre_repository.save(membre)
        await self._transaction.commit()
        return membre
