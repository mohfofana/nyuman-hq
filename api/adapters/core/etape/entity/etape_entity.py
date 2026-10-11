from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base, UtcDateTime


class EtapeEntity(Base):
    __tablename__ = "tache_etape"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tache_id: Mapped[int] = mapped_column(ForeignKey("tache.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    responsable_id: Mapped[Optional[int]] = mapped_column(ForeignKey("membre.id"), nullable=True)
    livrable: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="a_faire")
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    position: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    ref_externe: Mapped[Optional[str]] = mapped_column(String(80), nullable=True, unique=True)
    archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UtcDateTime, nullable=False)
