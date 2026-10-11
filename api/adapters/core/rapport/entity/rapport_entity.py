from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base, UtcDateTime


class RapportEntity(Base):
    __tablename__ = "rapport"
    __table_args__ = (UniqueConstraint("author_id", "week", name="uq_rapport_auteur_semaine"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("membre.id"), nullable=False, index=True)
    week: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    pole: Mapped[str] = mapped_column(String(20), nullable=False, default="")
    fait: Mapped[str] = mapped_column(Text, nullable=False, default="")
    en_cours: Mapped[str] = mapped_column(Text, nullable=False, default="")
    bloque: Mapped[str] = mapped_column(Text, nullable=False, default="")
    propositions: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(UtcDateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UtcDateTime, nullable=False)
