from typing import Dict, List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.core.decision.contract.decision_view_model import (
    BilanRequest,
    CreateDecisionRequest,
    DecisionViewModel,
    UpdateDecisionRequest,
    VoteRequest,
)
from adapters.core.decision.decision_app_config import DecisionAppConfig
from core.database import get_async_session
from core.session.session_middleware import get_current_membre
from domain.entities.decision import Decision
from domain.entities.membre import Membre

decision_router = APIRouter(prefix="/api/decisions", tags=["Salle du conseil"])


class DecisionController:
    def __init__(self, session: AsyncSession):
        self.config = DecisionAppConfig(session)

    async def membres(self) -> Dict[int, Membre]:
        return {m.id: m for m in await self.config.membre_repository.find_all()}

    async def view(self, decision: Decision) -> DecisionViewModel:
        votes = await self.config.decision_repository.votes_for([decision.id])
        return DecisionViewModel.of(decision, await self.membres(), votes.get(decision.id, []))


def decision_controller(session: AsyncSession = Depends(get_async_session)) -> DecisionController:
    return DecisionController(session)


@decision_router.get("", response_model=List[DecisionViewModel])
async def list_decisions(controller: DecisionController = Depends(decision_controller)) -> List[DecisionViewModel]:
    decisions, votes = await controller.config.get_conseil_use_case()()
    membres = await controller.membres()
    return [DecisionViewModel.of(d, membres, votes.get(d.id, [])) for d in decisions]


@decision_router.post("", response_model=DecisionViewModel, status_code=201)
async def create_decision(
    request: CreateDecisionRequest,
    actor: Membre = Depends(get_current_membre),
    controller: DecisionController = Depends(decision_controller),
) -> DecisionViewModel:
    decision = await controller.config.create_decision_use_case()(actor, request.to_input())
    return await controller.view(decision)


@decision_router.patch("/{decision_id}", response_model=DecisionViewModel)
async def update_decision(
    decision_id: int,
    request: UpdateDecisionRequest,
    actor: Membre = Depends(get_current_membre),
    controller: DecisionController = Depends(decision_controller),
) -> DecisionViewModel:
    decision = await controller.config.update_decision_use_case()(actor, decision_id, request.to_changes())
    return await controller.view(decision)


@decision_router.put("/{decision_id}/vote", response_model=DecisionViewModel)
async def vote_decision(
    decision_id: int,
    request: VoteRequest,
    actor: Membre = Depends(get_current_membre),
    controller: DecisionController = Depends(decision_controller),
) -> DecisionViewModel:
    await controller.config.vote_decision_use_case()(actor, decision_id, request.vote, request.commentaire)
    return await controller.view(await controller.config.decision_repository.find_by_id(decision_id))


@decision_router.put("/{decision_id}/bilan", response_model=DecisionViewModel)
async def bilan_decision(
    decision_id: int,
    request: BilanRequest,
    actor: Membre = Depends(get_current_membre),
    controller: DecisionController = Depends(decision_controller),
) -> DecisionViewModel:
    decision = await controller.config.bilan_decision_use_case()(actor, decision_id, request.verdict, request.bilan)
    return await controller.view(decision)


@decision_router.post("/{decision_id}/archiver", response_model=DecisionViewModel)
async def archive_decision(
    decision_id: int,
    actor: Membre = Depends(get_current_membre),
    controller: DecisionController = Depends(decision_controller),
) -> DecisionViewModel:
    decision = await controller.config.archive_decision_use_case()(actor, decision_id)
    return await controller.view(decision)
