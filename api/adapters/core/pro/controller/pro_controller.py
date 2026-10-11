from typing import Dict, List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.core.pro.contract.pro_view_model import CreateProRequest, ProViewModel, UpdateProRequest
from adapters.core.pro.pro_app_config import ProAppConfig
from core.database import get_async_session
from core.session.session_middleware import get_current_membre
from domain.entities.membre import Membre

# Le panel des pros contient des données personnelles (téléphones, emails) : toutes ces routes exigent une session,
# et aucune n'est ouverte aux agents tant que l'équipe ne l'a pas décidé.
pro_router = APIRouter(prefix="/api/pros", tags=["Panel des pros"])


class ProController:
    def __init__(self, session: AsyncSession):
        self.config = ProAppConfig(session)

    async def membres(self) -> Dict[int, Membre]:
        return {m.id: m for m in await self.config.membre_repository.find_all()}


def pro_controller(session: AsyncSession = Depends(get_async_session)) -> ProController:
    return ProController(session)


@pro_router.get("", response_model=List[ProViewModel])
async def list_pros(controller: ProController = Depends(pro_controller)) -> List[ProViewModel]:
    pros = await controller.config.get_pro_list_use_case()()
    membres = await controller.membres()
    return [ProViewModel.of(p, membres) for p in pros]


@pro_router.post("", response_model=ProViewModel, status_code=201)
async def create_pro(
    request: CreateProRequest,
    actor: Membre = Depends(get_current_membre),
    controller: ProController = Depends(pro_controller),
) -> ProViewModel:
    pro = await controller.config.create_pro_use_case()(actor, request.to_input())
    return ProViewModel.of(pro, await controller.membres())


@pro_router.patch("/{pro_id}", response_model=ProViewModel)
async def update_pro(
    pro_id: int,
    request: UpdateProRequest,
    actor: Membre = Depends(get_current_membre),
    controller: ProController = Depends(pro_controller),
) -> ProViewModel:
    pro = await controller.config.update_pro_use_case()(actor, pro_id, request.to_changes())
    return ProViewModel.of(pro, await controller.membres())


@pro_router.post("/{pro_id}/archiver", response_model=ProViewModel)
async def archive_pro(
    pro_id: int,
    actor: Membre = Depends(get_current_membre),
    controller: ProController = Depends(pro_controller),
) -> ProViewModel:
    pro = await controller.config.archive_pro_use_case()(actor, pro_id)
    return ProViewModel.of(pro, await controller.membres())
