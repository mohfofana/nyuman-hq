from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.core.objectif.entity.objectif_entity import ObjectifEntity
from domain.entities.objectif import Objectif
from use_cases.core.objectif.repository.objectif_repository import ObjectifRepository as ObjectifRepositoryInterface

_FIELDS = (
    "title", "quarter", "metric", "target", "start_date", "end_date", "pole", "current_manual",
    "created_by", "created_at", "updated_at",
)


class ObjectifRepository(ObjectifRepositoryInterface):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, objectif: Objectif) -> Objectif:
        entity = await self._session.get(ObjectifEntity, objectif.id) if objectif.id else None
        if entity is None:
            entity = ObjectifEntity()
            self._session.add(entity)
        for f in _FIELDS:
            setattr(entity, f, getattr(objectif, f))
        await self._session.flush()
        return self._to_domain(entity)

    async def find_by_id(self, objectif_id: int) -> Optional[Objectif]:
        entity = await self._session.get(ObjectifEntity, objectif_id)
        return self._to_domain(entity) if entity else None

    async def find_latest(self, pole: str = "") -> Optional[Objectif]:
        result = await self._session.execute(
            select(ObjectifEntity)
            .where(ObjectifEntity.pole == pole)
            .order_by(ObjectifEntity.end_date.desc(), ObjectifEntity.id.desc())
            .limit(1)
        )
        entity = result.scalar_one_or_none()
        return self._to_domain(entity) if entity else None

    @staticmethod
    def _to_domain(entity: ObjectifEntity) -> Objectif:
        return Objectif(id=entity.id, **{f: getattr(entity, f) for f in _FIELDS})
