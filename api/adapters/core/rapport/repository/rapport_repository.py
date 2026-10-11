from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.core.rapport.entity.rapport_entity import RapportEntity
from core.realtime.evenement_broadcast import mark_changed
from domain.entities.rapport import Rapport
from use_cases.core.rapport.repository.rapport_repository import RapportRepository as RapportRepositoryInterface

_FIELDS = ("author_id", "week", "pole", "fait", "en_cours", "bloque", "propositions", "created_at", "updated_at")


class RapportRepository(RapportRepositoryInterface):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, rapport: Rapport) -> Rapport:
        entity = await self._session.get(RapportEntity, rapport.id) if rapport.id else None
        if entity is None:
            entity = RapportEntity()
            self._session.add(entity)
        for f in _FIELDS:
            setattr(entity, f, getattr(rapport, f))
        await self._session.flush()
        mark_changed(self._session, "rapports")
        return self._to_domain(entity)

    async def find_by_author_week(self, author_id: int, week: str) -> Optional[Rapport]:
        result = await self._session.execute(
            select(RapportEntity).where(RapportEntity.author_id == author_id, RapportEntity.week == week)
        )
        entity = result.scalar_one_or_none()
        return self._to_domain(entity) if entity else None

    async def list_by_author(self, author_id: int, limit: int) -> List[Rapport]:
        result = await self._session.execute(
            select(RapportEntity).where(RapportEntity.author_id == author_id).order_by(RapportEntity.week.desc()).limit(limit)
        )
        return [self._to_domain(e) for e in result.scalars().all()]

    async def list_by_week(self, week: str) -> List[Rapport]:
        result = await self._session.execute(select(RapportEntity).where(RapportEntity.week == week))
        return [self._to_domain(e) for e in result.scalars().all()]

    @staticmethod
    def _to_domain(entity: RapportEntity) -> Rapport:
        return Rapport(id=entity.id, **{f: getattr(entity, f) for f in _FIELDS})
