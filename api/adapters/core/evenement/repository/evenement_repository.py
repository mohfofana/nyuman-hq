from typing import List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.core.evenement.entity.evenement_entity import EvenementEntity
from adapters.core.membre.entity.membre_entity import MembreEntity
from adapters.core.membre.entity.membre_mapper import MembreMapper
from core.realtime.evenement_broadcast import PENDING_KEY
from domain.entities.evenement import Evenement
from domain.entities.membre import Membre
from use_cases.core.evenement.repository.evenement_repository import (
    EvenementRepository as EvenementRepositoryInterface,
)

_FIELDS = ("actor_id", "verb", "text", "link", "created_at")


class EvenementRepository(EvenementRepositoryInterface):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, evenement: Evenement) -> None:
        entity = EvenementEntity(**{f: getattr(evenement, f) for f in _FIELDS})
        self._session.add(entity)
        await self._session.flush()
        # Diffusé en direct à tous les écrans juste après le commit (voir core/realtime/evenement_broadcast.py).
        self._session.info.setdefault(PENDING_KEY, []).append(entity)

    async def find_latest(self, limit: int, actor_id: Optional[int] = None) -> List[Tuple[Evenement, Membre]]:
        stmt = select(EvenementEntity, MembreEntity).join(MembreEntity, MembreEntity.id == EvenementEntity.actor_id)
        if actor_id is not None:
            stmt = stmt.where(EvenementEntity.actor_id == actor_id)
        result = await self._session.execute(
            stmt.order_by(EvenementEntity.created_at.desc(), EvenementEntity.id.desc()).limit(limit)
        )
        return [
            (Evenement(id=e.id, **{f: getattr(e, f) for f in _FIELDS}), MembreMapper.to_domain(m))
            for e, m in result.all()
        ]
