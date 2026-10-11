import re
from datetime import datetime
from typing import Dict, Literal

from pydantic import BaseModel, Field

from adapters.core.membre.contract.membre_view_model import MemberRefViewModel
from domain.entities.document import Document, DocumentVersion
from domain.entities.membre import Membre
from use_cases.core.document.document_input import DocumentInput

CategoryLiteral = Literal["cerveau", "contrats", "finances", "comptes-rendus", "specs", "pitch", "autre"]

_MARKDOWN = re.compile(r"[#*_>`|~\[\]]|^\s*[-+]\s+|^\s*\d+\.\s+|\(https?://[^)]*\)", re.MULTILINE)


def excerpt(content: str, size: int = 180) -> str:
    """Les premières phrases du document, sans les titres ni la mise en forme Markdown."""
    body = "\n".join(line for line in content.splitlines() if not line.lstrip().startswith("#"))
    text = " ".join(_MARKDOWN.sub(" ", body).split())
    return text if len(text) <= size else text[:size].rsplit(" ", 1)[0] + "…"


class DocumentSummaryViewModel(BaseModel):
    id: int
    title: str
    category: str
    version: int
    archived: bool
    excerpt: str
    updated_at: datetime
    updated_by: MemberRefViewModel

    @classmethod
    def of(cls, document: Document, membres: Dict[int, Membre]) -> "DocumentSummaryViewModel":
        return cls(
            id=document.id,
            title=document.title,
            category=document.category,
            version=document.version,
            archived=document.archived,
            excerpt=excerpt(document.content),
            updated_at=document.updated_at,
            updated_by=MemberRefViewModel.of(membres[document.updated_by]),
        )


class DocumentViewModel(DocumentSummaryViewModel):
    content: str
    created_at: datetime
    created_by: MemberRefViewModel

    @classmethod
    def of(cls, document: Document, membres: Dict[int, Membre]) -> "DocumentViewModel":
        summary = DocumentSummaryViewModel.of(document, membres)
        return cls(
            **summary.model_dump(exclude={"updated_by"}),
            updated_by=summary.updated_by,
            content=document.content,
            created_at=document.created_at,
            created_by=MemberRefViewModel.of(membres[document.created_by]),
        )


class DocumentVersionViewModel(BaseModel):
    version: int
    title: str
    author: MemberRefViewModel
    created_at: datetime

    @classmethod
    def of(cls, version: DocumentVersion, author: Membre) -> "DocumentVersionViewModel":
        return cls(
            version=version.version,
            title=version.title,
            author=MemberRefViewModel.of(author),
            created_at=version.created_at,
        )


class DocumentVersionFullViewModel(DocumentVersionViewModel):
    content: str

    @classmethod
    def of(cls, version: DocumentVersion, author: Membre) -> "DocumentVersionFullViewModel":
        return cls(**DocumentVersionViewModel.of(version, author).model_dump(exclude={"author"}),
                   author=MemberRefViewModel.of(author), content=version.content)


class CreateDocumentRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    category: CategoryLiteral
    content: str = Field(default="", max_length=500_000)

    def to_input(self) -> DocumentInput:
        return DocumentInput(title=self.title, category=self.category, content=self.content)


class UpdateDocumentRequest(CreateDocumentRequest):
    base_version: int = Field(ge=1)
