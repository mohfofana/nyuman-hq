from typing import Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.core.etape.entity.etape_entity import EtapeEntity
from core.realtime.evenement_broadcast import mark_changed
from domain.entities.etape import Etape
from use_cases.core.etape.repository.etape_repository import EtapeRepository as EtapeRepositoryInterface

_FIELDS = (
    "tache_id", "title", "responsable_id", "livrable", "status", "start_date", "due_date", "notes", "position",
    "ref_externe", "archived", "created_at", "updated_at",
)


class EtapeRepository(EtapeRepositoryInterface):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, etape: Etape) -> Etape:
        entity = await self._session.get(EtapeEntity, etape.id) if etape.id else None
        if entity is None:
            entity = EtapeEntity()
            self._session.add(entity)
        for f in _FIELDS:
            setattr(entity, f, getattr(etape, f))
        await self._session.flush()
        mark_changed(self._session, "taches")
        return self._to_domain(entity)

    async def find_by_id(self, etape_id: int) -> Optional[Etape]:
        entity = await self._session.get(EtapeEntity, etape_id)
        return self._to_domain(entity) if entity else None

    async def find_by_ref(self, ref_externe: str) -> Optional[Etape]:
        result = await self._session.execute(select(EtapeEntity).where(EtapeEntity.ref_externe == ref_externe))
        entity = result.scalar_one_or_none()
        return self._to_domain(entity) if entity else None

    async def list_for(self, tache_ids: List[int]) -> Dict[int, List[Etape]]:
        grouped: Dict[int, List[Etape]] = {i: [] for i in tache_ids}
        if not tache_ids:
            return grouped
        result = await self._session.execute(
            select(EtapeEntity)
            .where(EtapeEntity.tache_id.in_(tache_ids), EtapeEntity.archived.is_(False))
            .order_by(EtapeEntity.position.asc(), EtapeEntity.id.asc())
        )
        for entity in result.scalars().all():
            grouped[entity.tache_id].append(self._to_domain(entity))
        return grouped

    async def max_position(self, tache_id: int) -> float:
        result = await self._session.execute(
            select(func.max(EtapeEntity.position)).where(EtapeEntity.tache_id == tache_id)
        )
        return float(result.scalar_one() or 0)

    @staticmethod
    def _to_domain(entity: EtapeEntity) -> Etape:
        return Etape(id=entity.id, **{f: getattr(entity, f) for f in _FIELDS})
