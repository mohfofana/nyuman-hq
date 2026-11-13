from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Member(Base):
    """Un membre de l'équipe : humain ou agent, au même niveau."""

    __tablename__ = "members"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)  # ex. "kwame"
    name: Mapped[str] = mapped_column(String(80))
    kind: Mapped[str] = mapped_column(String(10))  # "human" | "agent"
    title: Mapped[str] = mapped_column(String(120))  # poste
    role: Mapped[str] = mapped_column(Text, default="")  # ce dont il s'occupe
    is_head: Mapped[bool] = mapped_column(Boolean, default=False)
    avatar_tone: Mapped[str] = mapped_column(String(20), default="neutral")
    now_doing: Mapped[str] = mapped_column(Text, default="")
    schedule: Mapped[str] = mapped_column(String(160), default="")  # créneaux
    # Statut choisi à la main (busy / dnd) ; la présence automatique vient du temps réel.
    manual_status: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    status_message: Mapped[str] = mapped_column(String(160), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
