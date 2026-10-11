from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from adapters.common.providers import get_stats_gateway
from use_cases.common.ports.out.stats_gateway import StatsGateway
from use_cases.core.kpi.get_kpis_use_case import GetKpisUseCase


class KpiViewModel(BaseModel):
    key: str
    label: str
    value: float
    unit: str


class KpisViewModel(BaseModel):
    available: bool
    reason: Optional[str]
    updated_at: Optional[datetime]
    values: List[KpiViewModel]


kpi_router = APIRouter(prefix="/api/kpis", tags=["KPI"])


@kpi_router.get("", response_model=KpisViewModel)
async def get_kpis(stats_gateway: StatsGateway = Depends(get_stats_gateway)) -> KpisViewModel:
    snapshot = await GetKpisUseCase(stats_gateway)()
    return KpisViewModel(
        available=snapshot.available,
        reason=snapshot.reason,
        updated_at=snapshot.updated_at,
        values=[KpiViewModel(key=k.key, label=k.label, value=k.value, unit=k.unit) for k in snapshot.values],
    )
