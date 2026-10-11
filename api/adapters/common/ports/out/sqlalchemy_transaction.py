from sqlalchemy.ext.asyncio import AsyncSession

from use_cases.common.ports.out.transaction import Transaction


class SqlAlchemyTransaction(Transaction):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def commit(self) -> None:
        await self._session.commit()
