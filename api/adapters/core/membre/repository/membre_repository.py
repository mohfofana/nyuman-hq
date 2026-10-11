from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.core.membre.entity.membre_entity import MembreEntity
from adapters.core.membre.entity.membre_mapper import MembreMapper
from domain.entities.membre import AGENT, HEAD, HUMAIN, Membre
from use_cases.core.membre.repository.membre_repository import MembreRepository as MembreRepositoryInterface


class MembreRepository(MembreRepositoryInterface):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, membre: Membre) -> Membre:
        entity = await self._session.get(MembreEntity, membre.id) if membre.id else None
        if entity is None:
            entity = MembreEntity()
            self._session.add(entity)
        MembreMapper.apply(membre, entity)
        await self._session.flush()
        return MembreMapper.to_domain(entity)

    async def find_by_id(self, membre_id: int) -> Optional[Membre]:
        entity = await self._session.get(MembreEntity, membre_id)
        return MembreMapper.to_domain(entity) if entity else None

    async def find_by_email(self, email: str) -> Optional[Membre]:
        result = await self._session.execute(select(MembreEntity).where(MembreEntity.email == email.lower()))
        entity = result.scalar_one_or_none()
        return MembreMapper.to_domain(entity) if entity else None

    async def find_all(self) -> List[Membre]:
        # Humains d'abord (heads en tête), puis les agents : tous dans la même liste.
        result = await self._session.execute(
            select(MembreEntity).order_by(
                (MembreEntity.kind == AGENT).asc(),
                (MembreEntity.role == HEAD).desc(),
                MembreEntity.id.asc(),
            )
        )
        return [MembreMapper.to_domain(e) for e in result.scalars().all()]

    async def count_active_heads(self) -> int:
        result = await self._session.execute(
            select(func.count()).select_from(MembreEntity).where(
                MembreEntity.kind == HUMAIN, MembreEntity.role == HEAD, MembreEntity.active.is_(True)
            )
        )
        return int(result.scalar_one())

    async def count_humans(self) -> int:
        result = await self._session.execute(
            select(func.count()).select_from(MembreEntity).where(MembreEntity.kind == HUMAIN)
        )
        return int(result.scalar_one())
