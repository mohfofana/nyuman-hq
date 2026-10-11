from datetime import date
from typing import Dict, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.common.providers import get_stats_gateway
from adapters.core.objectif.contract.objectif_view_model import (
    AvancementRequest,
    ObjectifViewModel,
    PoleParam,
    SaveObjectifRequest,
)
from adapters.core.objectif.objectif_app_config import ObjectifAppConfig
from core.database import get_async_session
from core.session.session_middleware import get_current_membre
from domain.entities.membre import Membre
from use_cases.common.ports.out.stats_gateway import StatsGateway

objectif_router = APIRouter(prefix="/api/objectifs", tags=["Objectifs"])


def objectif_config(
    session: AsyncSession = Depends(get_async_session),
    stats_gateway: StatsGateway = Depends(get_stats_gateway),
) -> ObjectifAppConfig:
    return ObjectifAppConfig(session, stats_gateway)


@objectif_router.get("/courant", response_model=Optional[ObjectifViewModel])
async def get_current(
    pole: PoleParam = Query(default="", description="Vide : l'objectif de toute la maison"),
    config: ObjectifAppConfig = Depends(objectif_config),
) -> Optional[ObjectifViewModel]:
    found = await config.get_current_objectif_use_case()(date.today(), pole)
    return ObjectifViewModel.of(*found) if found else None


@objectif_router.put("/courant", response_model=ObjectifViewModel)
async def save_current(
    request: SaveObjectifRequest,
    pole: PoleParam = Query(default=""),
    actor: Membre = Depends(get_current_membre),
    config: ObjectifAppConfig = Depends(objectif_config),
) -> ObjectifViewModel:
    await config.save_current_objectif_use_case()(actor, request.to_input(), date.today(), pole)
    found = await config.get_current_objectif_use_case()(date.today(), pole)
    return ObjectifViewModel.of(*found)


@objectif_router.get("/poles", response_model=Dict[str, ObjectifViewModel])
async def get_poles(config: ObjectifAppConfig = Depends(objectif_config)) -> Dict[str, ObjectifViewModel]:
    found = await config.get_pole_objectifs_use_case()(date.today())
    return {pole: ObjectifViewModel.of(o, s) for pole, (o, s) in found.items()}


@objectif_router.patch("/{objectif_id}/avancement", response_model=ObjectifViewModel)
async def update_avancement(
    objectif_id: int,
    request: AvancementRequest,
    actor: Membre = Depends(get_current_membre),
    config: ObjectifAppConfig = Depends(objectif_config),
) -> ObjectifViewModel:
    objectif = await config.update_avancement_use_case()(actor, objectif_id, request.value)
    found = await config.get_current_objectif_use_case()(date.today(), objectif.pole)
    return ObjectifViewModel.of(*found)
