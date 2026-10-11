from domain.value_objects.kpi import KpiSnapshot
from use_cases.common.ports.out.stats_gateway import StatsGateway


class GetKpisUseCase:
    def __init__(self, stats_gateway: StatsGateway):
        self._stats_gateway = stats_gateway

    async def __call__(self) -> KpiSnapshot:
        return await self._stats_gateway.snapshot()
