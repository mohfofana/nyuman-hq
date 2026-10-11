from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base, UtcDateTime


class LienEntity(Base):
    __tablename__ = "lien_connexion"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    membre_id: Mapped[int] = mapped_column(ForeignKey("membre.id"), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(UtcDateTime, nullable=False)
    used_at: Mapped[Optional[datetime]] = mapped_column(UtcDateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime, nullable=False)
