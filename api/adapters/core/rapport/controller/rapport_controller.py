from datetime import date, datetime
from typing import List

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.common.ports.out.sqlalchemy_transaction import SqlAlchemyTransaction
from adapters.core.evenement.repository.evenement_repository import EvenementRepository
from adapters.core.rapport.repository.rapport_repository import RapportRepository
from core.database import get_async_session
from core.session.session_middleware import get_current_membre
from domain.entities.membre import Membre
from domain.entities.rapport import Rapport, semaine_iso
from use_cases.core.rapport.rapport_use_cases import ContenuRapport, GetRapportsUseCase, PublishRapportUseCase

rapport_router = APIRouter(prefix="/api/rapports", tags=["Rapports de la semaine"])


class RapportViewModel(BaseModel):
    id: int
    author_id: int
    week: str
    pole: str
    fait: str
    en_cours: str
    bloque: str
    propositions: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def of(cls, r: Rapport) -> "RapportViewModel":
        return cls(id=r.id, **{f: getattr(r, f) for f in (
            "author_id", "week", "pole", "fait", "en_cours", "bloque", "propositions", "created_at", "updated_at")})


class SemaineViewModel(BaseModel):
    week: str
    rapports: List[RapportViewModel]


class PublishRapportRequest(BaseModel):
    fait: str = Field(default="", max_length=4000)
    en_cours: str = Field(default="", max_length=4000)
    bloque: str = Field(default="", max_length=4000)
    propositions: str = Field(default="", max_length=4000)


def _repo(session: AsyncSession = Depends(get_async_session)) -> RapportRepository:
    return RapportRepository(session)


@rapport_router.get("", response_model=List[RapportViewModel])
async def list_rapports(
    auteur: int = Query(..., description="Les rapports de ce membre, du plus récent au plus ancien"),
    limit: int = Query(default=8, ge=1, le=52),
    repo: RapportRepository = Depends(_repo),
) -> List[RapportViewModel]:
    return [RapportViewModel.of(r) for r in await GetRapportsUseCase(repo).by_author(auteur, limit)]


@rapport_router.get("/semaine", response_model=SemaineViewModel)
async def semaine(repo: RapportRepository = Depends(_repo)) -> SemaineViewModel:
    today = date.today()
    return SemaineViewModel(week=semaine_iso(today), rapports=[RapportViewModel.of(r) for r in await GetRapportsUseCase(repo).by_week(today)])


@rapport_router.put("/moi", response_model=RapportViewModel)
async def publish(
    request: PublishRapportRequest,
    actor: Membre = Depends(get_current_membre),
    session: AsyncSession = Depends(get_async_session),
) -> RapportViewModel:
    use_case = PublishRapportUseCase(RapportRepository(session), EvenementRepository(session), SqlAlchemyTransaction(session))
    rapport = await use_case(actor, ContenuRapport(**request.model_dump()), date.today())
    return RapportViewModel.of(rapport)
