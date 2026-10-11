from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.core.pro.entity.pro_entity import ProEntity
from core.realtime.evenement_broadcast import mark_changed
from domain.entities.pro import Pro
from use_cases.core.pro.repository.pro_repository import ProRepository as ProRepositoryInterface

_FIELDS = (
    "nom", "categorie", "enseigne", "audience", "telephone", "email", "contrat", "acces_test", "notes",
    "suivi_par_id", "numero", "ref_externe", "archived", "created_by", "created_at", "updated_at",
)


class ProRepository(ProRepositoryInterface):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, pro: Pro) -> Pro:
        entity = await self._session.get(ProEntity, pro.id) if pro.id else None
        if entity is None:
            entity = ProEntity()
            self._session.add(entity)
        for f in _FIELDS:
            setattr(entity, f, getattr(pro, f))
        await self._session.flush()
        mark_changed(self._session, "pros")
        return self._to_domain(entity)

    async def find_by_id(self, pro_id: int) -> Optional[Pro]:
        entity = await self._session.get(ProEntity, pro_id)
        return self._to_domain(entity) if entity else None

    async def find_by_ref(self, ref_externe: str) -> Optional[Pro]:
        result = await self._session.execute(select(ProEntity).where(ProEntity.ref_externe == ref_externe))
        entity = result.scalar_one_or_none()
        return self._to_domain(entity) if entity else None

    async def list_active(self) -> List[Pro]:
        result = await self._session.execute(
            select(ProEntity)
            .where(ProEntity.archived.is_(False))
            .order_by(ProEntity.numero.asc().nulls_last(), ProEntity.id.asc())
        )
        return [self._to_domain(e) for e in result.scalars().all()]

    @staticmethod
    def _to_domain(entity: ProEntity) -> Pro:
        return Pro(id=entity.id, **{f: getattr(entity, f) for f in _FIELDS})
