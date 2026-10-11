from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.core.tache.contract.tache_view_model import (
    CreateEtapeRequest,
    CreateTacheRequest,
    TacheViewModel,
    UpdateEtapeRequest,
    UpdateTacheRequest,
)
from adapters.core.tache.tache_app_config import TacheAppConfig
from core.database import get_async_session
from core.session.session_middleware import get_current_membre
from domain.entities.membre import Membre
from domain.entities.tache import Tache

tache_router = APIRouter(prefix="/api/taches", tags=["Salle de projet"])


class TacheController:
    def __init__(self, session: AsyncSession):
        self.config = TacheAppConfig(session)

    async def membres(self) -> Dict[int, Membre]:
        return {m.id: m for m in await self.config.membre_repository.find_all()}

    async def views(self, taches: List[Tache]) -> List[TacheViewModel]:
        membres = await self.membres()
        etapes = await self.config.etape_repository.list_for([t.id for t in taches])
        return [TacheViewModel.of(t, membres, etapes.get(t.id, [])) for t in taches]

    async def view(self, tache: Tache) -> TacheViewModel:
        return (await self.views([tache]))[0]

    async def view_by_id(self, tache_id: int) -> TacheViewModel:
        return await self.view(await self.config.tache_repository.find_by_id(tache_id))


def tache_controller(session: AsyncSession = Depends(get_async_session)) -> TacheController:
    return TacheController(session)


@tache_router.get("", response_model=List[TacheViewModel])
async def list_taches(
    assignee: Optional[int] = Query(default=None, description="Seulement les tâches de ce membre"),
    archives: bool = False,
    controller: TacheController = Depends(tache_controller),
) -> List[TacheViewModel]:
    taches = await controller.config.get_tache_list_use_case()(assignee, archives)
    return await controller.views(taches)


@tache_router.post("", response_model=TacheViewModel, status_code=201)
async def create_tache(
    request: CreateTacheRequest,
    actor: Membre = Depends(get_current_membre),
    controller: TacheController = Depends(tache_controller),
) -> TacheViewModel:
    tache = await controller.config.create_tache_use_case()(actor, request.to_input())
    return await controller.view(tache)


@tache_router.patch("/{tache_id}", response_model=TacheViewModel)
async def update_tache(
    tache_id: int,
    request: UpdateTacheRequest,
    actor: Membre = Depends(get_current_membre),
    controller: TacheController = Depends(tache_controller),
) -> TacheViewModel:
    tache = await controller.config.update_tache_use_case()(actor, tache_id, request.to_changes())
    return await controller.view(tache)


@tache_router.post("/{tache_id}/archiver", response_model=TacheViewModel)
async def archive_tache(
    tache_id: int,
    actor: Membre = Depends(get_current_membre),
    controller: TacheController = Depends(tache_controller),
) -> TacheViewModel:
    tache = await controller.config.archive_tache_use_case()(actor, tache_id)
    return await controller.view(tache)


@tache_router.post("/{tache_id}/etapes", response_model=TacheViewModel, status_code=201)
async def add_etape(
    tache_id: int,
    request: CreateEtapeRequest,
    actor: Membre = Depends(get_current_membre),
    controller: TacheController = Depends(tache_controller),
) -> TacheViewModel:
    await controller.config.add_etape_use_case()(actor, tache_id, request.to_input())
    return await controller.view_by_id(tache_id)


@tache_router.patch("/{tache_id}/etapes/{etape_id}", response_model=TacheViewModel)
async def update_etape(
    tache_id: int,
    etape_id: int,
    request: UpdateEtapeRequest,
    actor: Membre = Depends(get_current_membre),
    controller: TacheController = Depends(tache_controller),
) -> TacheViewModel:
    await controller.config.update_etape_use_case()(actor, tache_id, etape_id, request.to_changes())
    return await controller.view_by_id(tache_id)


@tache_router.post("/{tache_id}/etapes/{etape_id}/archiver", response_model=TacheViewModel)
async def archive_etape(
    tache_id: int,
    etape_id: int,
    actor: Membre = Depends(get_current_membre),
    controller: TacheController = Depends(tache_controller),
) -> TacheViewModel:
    await controller.config.archive_etape_use_case()(actor, tache_id, etape_id)
    return await controller.view_by_id(tache_id)
