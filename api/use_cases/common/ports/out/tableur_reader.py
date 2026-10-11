from abc import ABC, abstractmethod
from typing import Any, Dict, List

from core.exceptions import BusinessException, ErrorType

# Un classeur lu : pour chaque onglet, ses lignes de cellules (texte, nombre, date ou None), dans l'ordre.
Classeur = Dict[str, List[List[Any]]]


class TableurIllisibleException(BusinessException):
    def __init__(self, message: str = "Ce fichier ne se lit pas. Envoie le tableau au format Excel (.xlsx)."):
        super().__init__(message, ErrorType.VALIDATION_ERROR)


class TableurReader(ABC):
    @abstractmethod
    def read(self, content: bytes) -> Classeur: ...
