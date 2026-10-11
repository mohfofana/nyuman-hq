from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base, UtcDateTime


class RetourEntity(Base):
    __tablename__ = "retour"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    kind: Mapped[str] = mapped_column(String(20), nullable=False)
    source: Mapped[str] = mapped_column(String(20), nullable=False)
    comment: Mapped[str] = mapped_column(Text, nullable=False, default="")
    author_id: Mapped[Optional[int]] = mapped_column(ForeignKey("membre.id"), nullable=True)
    tester_email: Mapped[Optional[str]] = mapped_column(String(254), nullable=True)
    espace: Mapped[str] = mapped_column(String(20), nullable=False, default="")
    device_model: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    os_version: Mapped[str] = mapped_column(String(40), nullable=False, default="")
    build_version: Mapped[str] = mapped_column(String(40), nullable=False, default="")
    captures: Mapped[str] = mapped_column(Text, nullable=False, default="[]")  # liste JSON des fichiers
    statut: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    tache_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    asc_id: Mapped[Optional[str]] = mapped_column(String(80), nullable=True, unique=True)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime, nullable=False, index=True)
