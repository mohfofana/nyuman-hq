from typing import Optional

from domain.entities.membre import HEAD, HUMAIN, MEMBRE, POLES, Membre
from use_cases.common.ports.out.transaction import Transaction
from use_cases.core.membre.exceptions.membre_exceptions import (
    MembreNotFoundException,
    ModificationInterditeException,
    ReserveAuxHeadsException,
)
from use_cases.core.membre.repository.membre_repository import MembreRepository


class UpdateMembreUseCase:
    """Un head règle les droits, le rôle et le pôle des humains et le pôle des agents ; la maison garde toujours un head.

    Chacun peut aussi corriger son propre rôle affiché et son pôle (jamais ses droits).
    """

    def __init__(self, membre_repository: MembreRepository, transaction: Transaction):
        self._membre_repository = membre_repository
        self._transaction = transaction

    async def __call__(
        self,
        actor: Membre,
        membre_id: int,
        role: Optional[str] = None,
        title: Optional[str] = None,
        active: Optional[bool] = None,
        pole: Optional[str] = None,
    ) -> Membre:
        membre = await self._membre_repository.find_by_id(membre_id)
        if membre is None:
            raise MembreNotFoundException()
        self_edit = membre.id == actor.id
        if self_edit:
            if role is not None or active is not None:
                raise ModificationInterditeException("Tu ne peux pas changer tes propres droits.")
        elif not actor.is_head:
            raise ReserveAuxHeadsException()
        if membre.kind != HUMAIN and (role is not None or active is not None or title is not None):
            raise ModificationInterditeException("Pour un agent, seul le pôle se règle ici.")
        if role is not None and role not in (HEAD, MEMBRE):
            raise ModificationInterditeException("Les droits possibles sont « head » ou « membre ».")
        if pole is not None and pole not in POLES and pole != "":
            raise ModificationInterditeException("Ce pôle n’existe pas.")

        loses_head = membre.is_head and membre.active and (role == MEMBRE or active is False)
        if loses_head and await self._membre_repository.count_active_heads() <= 1:
            raise ModificationInterditeException("La maison doit garder au moins un head.")

        if role is not None:
            membre.role = role
        if title is not None:
            membre.title = title.strip()
        if active is not None:
            membre.active = active
        if pole is not None:
            membre.pole = pole
        membre = await self._membre_repository.save(membre)
        await self._transaction.commit()
        return membre
