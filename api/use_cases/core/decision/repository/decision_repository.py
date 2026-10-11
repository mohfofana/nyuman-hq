from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from domain.entities.decision import Decision, Vote


class DecisionRepository(ABC):
    @abstractmethod
    async def save(self, decision: Decision) -> Decision: ...

    @abstractmethod
    async def find_by_id(self, decision_id: int) -> Optional[Decision]: ...

    @abstractmethod
    async def find_by_ref(self, ref_externe: str) -> Optional[Decision]: ...

    @abstractmethod
    async def list_active(self) -> List[Decision]: ...

    @abstractmethod
    async def save_vote(self, vote: Vote) -> Vote: ...

    @abstractmethod
    async def find_vote(self, decision_id: int, membre_id: int) -> Optional[Vote]: ...

    @abstractmethod
    async def votes_for(self, decision_ids: List[int]) -> Dict[int, List[Vote]]: ...
