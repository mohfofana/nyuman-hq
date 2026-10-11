from datetime import datetime, timedelta, timezone

from domain.entities.membre import Membre
from use_cases.common.ports.out.transaction import Transaction
from use_cases.core.membre.repository.membre_repository import MembreRepository

# On n'écrit la présence qu'une fois par minute, pas à chaque requête.
_INTERVALLE = timedelta(minutes=1)


class MarkPresenceUseCase:
    def __init__(self, membre_repository: MembreRepository, transaction: Transaction):
        self._membre_repository = membre_repository
        self._transaction = transaction

    async def __call__(self, membre: Membre) -> Membre:
        now = datetime.now(timezone.utc)
        if membre.last_seen_at and now - membre.last_seen_at < _INTERVALLE:
            return membre
        membre.last_seen_at = now
        membre = await self._membre_repository.save(membre)
        await self._transaction.commit()
        return membre
