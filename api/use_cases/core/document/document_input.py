from dataclasses import dataclass

from domain.entities.document import CATEGORIES
from use_cases.core.document.exceptions.document_exceptions import DocumentInvalideException


@dataclass
class DocumentInput:
    title: str
    category: str
    content: str

    def validated(self) -> "DocumentInput":
        title = self.title.strip()
        if not title:
            raise DocumentInvalideException("Le document a besoin d’un titre.")
        if self.category not in CATEGORIES:
            raise DocumentInvalideException("Ce rayon n’existe pas dans la bibliothèque.")
        return DocumentInput(title=title, category=self.category, content=self.content)
