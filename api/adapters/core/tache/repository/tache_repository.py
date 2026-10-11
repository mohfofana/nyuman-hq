from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.core.tache.entity.tache_entity import TacheEntity
from core.realtime.evenement_broadcast import mark_changed
from domain.entities.tache import Tache
from use_cases.core.tache.repository.tache_repository import TacheRepository as TacheRepositoryInterface

_FIELDS = (
    "title", "description", "status", "assignee_id", "pole", "due_date", "priority", "objectif_id", "position",
    "source", "retour_id", "ref_externe", "archived", "created_by", "created_at", "updated_at", "done_at",
)


class TacheRepository(TacheRepositoryInterface):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, tache: Tache) -> Tache:
        entity = await self._session.get(TacheEntity, tache.id) if tache.id else None
        if entity is None:
            entity = TacheEntity()
            self._session.add(entity)
        for f in _FIELDS:
            setattr(entity, f, getattr(tache, f))
        await self._session.flush()
        mark_changed(self._session, "taches")
        return self._to_domain(entity)

    async def find_by_id(self, tache_id: int) -> Optional[Tache]:
        entity = await self._session.get(TacheEntity, tache_id)
        return self._to_domain(entity) if entity else None

    async def search(self, assignee_id: Optional[int], archived: bool) -> List[Tache]:
        stmt = select(TacheEntity).where(TacheEntity.archived.is_(archived))
        if assignee_id is not None:
            stmt = stmt.where(TacheEntity.assignee_id == assignee_id)
        result = await self._session.execute(stmt.order_by(TacheEntity.position.asc(), TacheEntity.id.asc()))
        return [self._to_domain(e) for e in result.scalars().all()]

    async def find_by_ref(self, ref_externe: str) -> Optional[Tache]:
        result = await self._session.execute(select(TacheEntity).where(TacheEntity.ref_externe == ref_externe))
        entity = result.scalar_one_or_none()
        return self._to_domain(entity) if entity else None

    async def max_position(self, status: str) -> float:
        result = await self._session.execute(select(func.max(TacheEntity.position)).where(TacheEntity.status == status))
        return float(result.scalar_one() or 0)

    @staticmethod
    def _to_domain(entity: TacheEntity) -> Tache:
        return Tache(id=entity.id, **{f: getattr(entity, f) for f in _FIELDS})
