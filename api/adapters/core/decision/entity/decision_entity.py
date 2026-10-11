from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base, UtcDateTime


class DecisionEntity(Base):
    __tablename__ = "decision"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    titre: Mapped[str] = mapped_column(String(200), nullable=False)
    demande: Mapped[str] = mapped_column(Text, nullable=False, default="")
    pole_concerne: Mapped[str] = mapped_column(String(20), nullable=False, default="")
    poles_en_charge: Mapped[str] = mapped_column(String(100), nullable=False, default="")  # séparés par des virgules
    objectif: Mapped[str] = mapped_column(Text, nullable=False, default="")
    risques: Mapped[str] = mapped_column(Text, nullable=False, default="")
    decision: Mapped[str] = mapped_column(Text, nullable=False, default="")
    liens: Mapped[str] = mapped_column(Text, nullable=False, default="")
    statut: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    date_demande: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    decided_at: Mapped[Optional[datetime]] = mapped_column(UtcDateTime, nullable=True)
    decided_by: Mapped[Optional[int]] = mapped_column(ForeignKey("membre.id"), nullable=True)
    bilan: Mapped[str] = mapped_column(Text, nullable=False, default="")
    bilan_verdict: Mapped[str] = mapped_column(String(20), nullable=False, default="")
    bilan_at: Mapped[Optional[datetime]] = mapped_column(UtcDateTime, nullable=True)
    ref_externe: Mapped[Optional[str]] = mapped_column(String(80), nullable=True, unique=True)
    archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    author_id: Mapped[int] = mapped_column(ForeignKey("membre.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UtcDateTime, nullable=False)


class VoteEntity(Base):
    __tablename__ = "decision_vote"
    __table_args__ = (UniqueConstraint("decision_id", "membre_id", name="uq_vote_decision_membre"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    decision_id: Mapped[int] = mapped_column(ForeignKey("decision.id"), nullable=False, index=True)
    membre_id: Mapped[int] = mapped_column(ForeignKey("membre.id"), nullable=False)
    vote: Mapped[str] = mapped_column(String(20), nullable=False)
    commentaire: Mapped[str] = mapped_column(Text, nullable=False, default="")
    updated_at: Mapped[datetime] = mapped_column(UtcDateTime, nullable=False)
