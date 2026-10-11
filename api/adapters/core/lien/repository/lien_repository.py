from datetime import datetime
from typing import Optional

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.core.lien.entity.lien_entity import LienEntity
from domain.entities.lien_connexion import LienConnexion
from use_cases.core.lien.repository.lien_repository import LienRepository as LienRepositoryInterface

_FIELDS = ("membre_id", "token_hash", "expires_at", "used_at", "created_at")


class LienRepository(LienRepositoryInterface):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, lien: LienConnexion) -> LienConnexion:
        entity = LienEntity(**{f: getattr(lien, f) for f in _FIELDS})
        self._session.add(entity)
        await self._session.flush()
        return self._to_domain(entity)

    async def find_by_hash(self, token_hash: str) -> Optional[LienConnexion]:
        result = await self._session.execute(select(LienEntity).where(LienEntity.token_hash == token_hash))
        entity = result.scalar_one_or_none()
        return self._to_domain(entity) if entity else None

    async def count_since(self, membre_id: int, since: datetime) -> int:
        result = await self._session.execute(
            select(func.count())
            .select_from(LienEntity)
            .where(LienEntity.membre_id == membre_id, LienEntity.created_at >= since)
        )
        return int(result.scalar_one())

    async def consommer(self, lien_id: int, now: datetime) -> bool:
        # Une seule requête « si pas encore utilisé » : deux clics en même temps ne donnent qu'une session.
        result = await self._session.execute(
            update(LienEntity).where(LienEntity.id == lien_id, LienEntity.used_at.is_(None)).values(used_at=now)
        )
        return result.rowcount == 1

    async def annuler_restants(self, membre_id: int, now: datetime) -> None:
        await self._session.execute(
            update(LienEntity)
            .where(LienEntity.membre_id == membre_id, LienEntity.used_at.is_(None))
            .values(used_at=now)
        )

    async def purger(self, before: datetime) -> None:
        await self._session.execute(delete(LienEntity).where(LienEntity.expires_at < before))

    @staticmethod
    def _to_domain(entity: LienEntity) -> LienConnexion:
        return LienConnexion(id=entity.id, **{f: getattr(entity, f) for f in _FIELDS})
