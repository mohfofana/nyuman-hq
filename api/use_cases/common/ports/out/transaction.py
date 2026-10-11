from abc import ABC, abstractmethod


class Transaction(ABC):
    """Valide d'un coup tout ce qu'un use case a écrit (document, version et événement ensemble)."""

    @abstractmethod
    async def commit(self) -> None: ...
