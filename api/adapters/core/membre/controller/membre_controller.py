from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.core.membre.contract.membre_view_model import AddMembreRequest, MemberViewModel, UpdateMembreRequest
from adapters.core.membre.membre_app_config import MembreAppConfig
from core.database import get_async_session
from core.session.session_middleware import get_current_membre
from domain.entities.membre import Membre

membre_router = APIRouter(prefix="/api/membres", tags=["Membres"])


def membre_config(session: AsyncSession = Depends(get_async_session)) -> MembreAppConfig:
    return MembreAppConfig(session)


@membre_router.get("", response_model=List[MemberViewModel])
async def list_membres(config: MembreAppConfig = Depends(membre_config)) -> List[MemberViewModel]:
    return [MemberViewModel.of(m) for m in await config.get_membre_list_use_case()()]


@membre_router.post("", response_model=MemberViewModel, status_code=201)
async def add_membre(
    request: AddMembreRequest,
    actor: Membre = Depends(get_current_membre),
    config: MembreAppConfig = Depends(membre_config),
) -> MemberViewModel:
    membre = await config.add_membre_use_case()(
        actor, email=request.email, name=request.name, title=request.title, role=request.role, pole=request.pole
    )
    return MemberViewModel.of(membre)


@membre_router.patch("/{membre_id}", response_model=MemberViewModel)
async def update_membre(
    membre_id: int,
    request: UpdateMembreRequest,
    actor: Membre = Depends(get_current_membre),
    config: MembreAppConfig = Depends(membre_config),
) -> MemberViewModel:
    membre = await config.update_membre_use_case()(
        actor, membre_id, role=request.role, title=request.title, active=request.active, pole=request.pole
    )
    return MemberViewModel.of(membre)
