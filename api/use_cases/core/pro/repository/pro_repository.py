from abc import ABC, abstractmethod
from typing import List, Optional

from domain.entities.pro import Pro


class ProRepository(ABC):
    @abstractmethod
    async def save(self, pro: Pro) -> Pro: ...

    @abstractmethod
    async def find_by_id(self, pro_id: int) -> Optional[Pro]: ...

    @abstractmethod
    async def find_by_ref(self, ref_externe: str) -> Optional[Pro]: ...

    @abstractmethod
    async def list_active(self) -> List[Pro]: ...
