from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.core.evenement.repository.evenement_repository import EvenementRepository
from adapters.core.membre.contract.membre_view_model import MemberRefViewModel
from core.database import get_async_session
from use_cases.core.evenement.get_evenement_list_use_case import GetEvenementListUseCase


class EvenementViewModel(BaseModel):
    id: int
    actor: MemberRefViewModel
    text: str
    link: Optional[str]
    created_at: datetime


evenement_router = APIRouter(prefix="/api/evenements", tags=["Fil de la maison"])


@evenement_router.get("", response_model=List[EvenementViewModel])
async def list_evenements(
    acteur: Optional[int] = Query(default=None, description="Seulement les actions de ce membre (son bureau)"),
    limit: int = Query(default=30, ge=1, le=100),
    session: AsyncSession = Depends(get_async_session),
) -> List[EvenementViewModel]:
    rows = await GetEvenementListUseCase(EvenementRepository(session))(limit, acteur)
    return [
        EvenementViewModel(
            id=e.id, actor=MemberRefViewModel.of(actor), text=e.text, link=e.link, created_at=e.created_at
        )
        for e, actor in rows
    ]
