from typing import Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.core.decision.entity.decision_entity import DecisionEntity, VoteEntity
from core.realtime.evenement_broadcast import mark_changed
from domain.entities.decision import Decision, Vote
from use_cases.core.decision.repository.decision_repository import DecisionRepository as DecisionRepositoryInterface

_FIELDS = (
    "titre", "demande", "pole_concerne", "objectif", "risques", "decision", "liens", "statut", "date_demande",
    "decided_at", "decided_by", "bilan", "bilan_verdict", "bilan_at", "ref_externe", "archived", "author_id",
    "created_at", "updated_at",
)
_VOTE_FIELDS = ("decision_id", "membre_id", "vote", "commentaire", "updated_at")


class DecisionRepository(DecisionRepositoryInterface):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, decision: Decision) -> Decision:
        entity = await self._session.get(DecisionEntity, decision.id) if decision.id else None
        if entity is None:
            entity = DecisionEntity()
            self._session.add(entity)
        for f in _FIELDS:
            setattr(entity, f, getattr(decision, f))
        entity.poles_en_charge = ",".join(decision.poles_en_charge)
        await self._session.flush()
        mark_changed(self._session, "decisions")
        return self._to_domain(entity)

    async def find_by_id(self, decision_id: int) -> Optional[Decision]:
        entity = await self._session.get(DecisionEntity, decision_id)
        return self._to_domain(entity) if entity else None

    async def find_by_ref(self, ref_externe: str) -> Optional[Decision]:
        result = await self._session.execute(select(DecisionEntity).where(DecisionEntity.ref_externe == ref_externe))
        entity = result.scalar_one_or_none()
        return self._to_domain(entity) if entity else None

    async def list_active(self) -> List[Decision]:
        result = await self._session.execute(
            select(DecisionEntity)
            .where(DecisionEntity.archived.is_(False))
            .order_by(DecisionEntity.date_demande.desc().nulls_last(), DecisionEntity.id.desc())
        )
        return [self._to_domain(e) for e in result.scalars().all()]

    async def save_vote(self, vote: Vote) -> Vote:
        entity = await self._session.get(VoteEntity, vote.id) if vote.id else None
        if entity is None:
            entity = VoteEntity()
            self._session.add(entity)
        for f in _VOTE_FIELDS:
            setattr(entity, f, getattr(vote, f))
        await self._session.flush()
        mark_changed(self._session, "decisions")
        return self._vote(entity)

    async def find_vote(self, decision_id: int, membre_id: int) -> Optional[Vote]:
        result = await self._session.execute(
            select(VoteEntity).where(VoteEntity.decision_id == decision_id, VoteEntity.membre_id == membre_id)
        )
        entity = result.scalar_one_or_none()
        return self._vote(entity) if entity else None

    async def votes_for(self, decision_ids: List[int]) -> Dict[int, List[Vote]]:
        grouped: Dict[int, List[Vote]] = {i: [] for i in decision_ids}
        if not decision_ids:
            return grouped
        result = await self._session.execute(
            select(VoteEntity).where(VoteEntity.decision_id.in_(decision_ids)).order_by(VoteEntity.updated_at.asc())
        )
        for entity in result.scalars().all():
            grouped[entity.decision_id].append(self._vote(entity))
        return grouped

    @staticmethod
    def _to_domain(entity: DecisionEntity) -> Decision:
        data = {f: getattr(entity, f) for f in _FIELDS}
        poles = [p for p in (entity.poles_en_charge or "").split(",") if p]
        return Decision(id=entity.id, poles_en_charge=poles, **data)

    @staticmethod
    def _vote(entity: VoteEntity) -> Vote:
        return Vote(id=entity.id, **{f: getattr(entity, f) for f in _VOTE_FIELDS})
