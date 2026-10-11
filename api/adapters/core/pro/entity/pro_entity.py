from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base, UtcDateTime


class ProEntity(Base):
    __tablename__ = "pro"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nom: Mapped[str] = mapped_column(String(120), nullable=False)
    categorie: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    enseigne: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    audience: Mapped[str] = mapped_column(String(40), nullable=False, default="")
    telephone: Mapped[str] = mapped_column(String(40), nullable=False, default="")
    email: Mapped[str] = mapped_column(String(254), nullable=False, default="")
    contrat: Mapped[str] = mapped_column(String(20), nullable=False, default="")
    acces_test: Mapped[str] = mapped_column(String(20), nullable=False, default="")
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    suivi_par_id: Mapped[Optional[int]] = mapped_column(ForeignKey("membre.id"), nullable=True)
    numero: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ref_externe: Mapped[Optional[str]] = mapped_column(String(80), nullable=True, unique=True)
    archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_by: Mapped[int] = mapped_column(ForeignKey("membre.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UtcDateTime, nullable=False)
