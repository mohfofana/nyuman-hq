from datetime import datetime, timezone
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field

from domain.entities.membre import STATUS_LABELS, Membre


class MemberRefViewModel(BaseModel):
    id: int
    name: str
    kind: str
    initials: str
    color: str

    @classmethod
    def of(cls, membre: Membre) -> "MemberRefViewModel":
        return cls(id=membre.id, name=membre.name, kind=membre.kind, initials=membre.initials, color=membre.color)


class MemberViewModel(MemberRefViewModel):
    email: Optional[str]
    role: str
    title: str
    pole: str
    status: str
    status_label: str
    active: bool

    @classmethod
    def of(cls, membre: Membre) -> "MemberViewModel":
        status = membre.current_status(datetime.now(timezone.utc))
        return cls(
            id=membre.id,
            name=membre.name,
            kind=membre.kind,
            initials=membre.initials,
            color=membre.color,
            email=membre.email,
            role=membre.role,
            title=membre.title,
            pole=membre.pole,
            status=status,
            status_label=STATUS_LABELS.get(status, status),
            active=membre.active,
        )


PoleLiteral = Literal["direction", "operations", "produit", "croissance", ""]


class AddMembreRequest(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=120)
    title: str = Field(default="", max_length=120)
    role: Literal["head", "membre"] = "membre"
    pole: PoleLiteral = ""


class UpdateMembreRequest(BaseModel):
    role: Optional[Literal["head", "membre"]] = None
    title: Optional[str] = Field(default=None, max_length=120)
    active: Optional[bool] = None
    pole: Optional[PoleLiteral] = None
