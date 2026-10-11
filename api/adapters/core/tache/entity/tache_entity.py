from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base, UtcDateTime


class TacheEntity(Base):
    __tablename__ = "tache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    assignee_id: Mapped[Optional[int]] = mapped_column(ForeignKey("membre.id"), nullable=True, index=True)
    pole: Mapped[str] = mapped_column(String(20), nullable=False, default="", server_default="", index=True)
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    priority: Mapped[str] = mapped_column(String(4), nullable=False, default="", server_default="")
    objectif_id: Mapped[Optional[int]] = mapped_column(ForeignKey("objectif.id"), nullable=True)
    position: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="humain")
    retour_id: Mapped[Optional[int]] = mapped_column(ForeignKey("retour.id"), nullable=True)
    ref_externe: Mapped[Optional[str]] = mapped_column(String(80), nullable=True, unique=True)
    archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_by: Mapped[int] = mapped_column(ForeignKey("membre.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UtcDateTime, nullable=False)
    done_at: Mapped[Optional[datetime]] = mapped_column(UtcDateTime, nullable=True)
