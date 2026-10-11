from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base, UtcDateTime


class ObjectifEntity(Base):
    __tablename__ = "objectif"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    quarter: Mapped[str] = mapped_column(String(20), nullable=False)
    metric: Mapped[str] = mapped_column(String(40), nullable=False)
    target: Mapped[float] = mapped_column(Float, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    pole: Mapped[str] = mapped_column(String(20), nullable=False, default="", server_default="", index=True)
    current_manual: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("membre.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UtcDateTime, nullable=False)
