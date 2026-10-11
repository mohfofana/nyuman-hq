import json
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.core.retour.entity.retour_entity import RetourEntity
from core.realtime.evenement_broadcast import mark_changed
from domain.entities.retour import Retour
from use_cases.core.retour.repository.retour_repository import RetourRepository as RetourRepositoryInterface

_FIELDS = (
    "kind", "source", "comment", "author_id", "tester_email", "espace", "device_model", "os_version",
    "build_version", "statut", "tache_id", "asc_id", "created_at",
)


class RetourRepository(RetourRepositoryInterface):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, retour: Retour) -> Retour:
        entity = await self._session.get(RetourEntity, retour.id) if retour.id else None
        if entity is None:
            entity = RetourEntity()
            self._session.add(entity)
        for f in _FIELDS:
            setattr(entity, f, getattr(retour, f))
        entity.captures = json.dumps(retour.captures)
        await self._session.flush()
        mark_changed(self._session, "retours")
        return self._to_domain(entity)

    async def find_by_id(self, retour_id: int) -> Optional[Retour]:
        entity = await self._session.get(RetourEntity, retour_id)
        return self._to_domain(entity) if entity else None

    async def known_asc_ids(self) -> set:
        result = await self._session.execute(select(RetourEntity.asc_id).where(RetourEntity.asc_id.is_not(None)))
        return set(result.scalars().all())

    async def search(self, statut: Optional[str]) -> List[Retour]:
        stmt = select(RetourEntity)
        if statut:
            stmt = stmt.where(RetourEntity.statut == statut)
        result = await self._session.execute(stmt.order_by(RetourEntity.created_at.desc(), RetourEntity.id.desc()))
        return [self._to_domain(e) for e in result.scalars().all()]

    async def count(self, statut: str) -> int:
        result = await self._session.execute(
            select(func.count()).select_from(RetourEntity).where(RetourEntity.statut == statut)
        )
        return int(result.scalar_one())

    @staticmethod
    def _to_domain(entity: RetourEntity) -> Retour:
        return Retour(id=entity.id, captures=json.loads(entity.captures or "[]"), **{f: getattr(entity, f) for f in _FIELDS})
