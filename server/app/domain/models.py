from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
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


def _uuid() -> str:
    import uuid

    return uuid.uuid4().hex


class Channel(Base):
    """Un canal d'équipe (ouvert à tous) ou une discussion privée (dm)."""

    __tablename__ = "channels"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    kind: Mapped[str] = mapped_column(String(10))  # "channel" | "dm"
    name: Mapped[str] = mapped_column(String(80), default="")
    topic: Mapped[str] = mapped_column(String(200), default="")
    created_by: Mapped[Optional[str]] = mapped_column(ForeignKey("members.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ChannelMember(Base):
    __tablename__ = "channel_members"

    channel_id: Mapped[str] = mapped_column(ForeignKey("channels.id", ondelete="CASCADE"), primary_key=True)
    member_id: Mapped[str] = mapped_column(ForeignKey("members.id"), primary_key=True)
    last_read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    channel_id: Mapped[str] = mapped_column(ForeignKey("channels.id", ondelete="CASCADE"), index=True)
    author_id: Mapped[str] = mapped_column(ForeignKey("members.id"))
    parent_id: Mapped[Optional[str]] = mapped_column(ForeignKey("messages.id"), nullable=True, index=True)
    body: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    edited_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted: Mapped[bool] = mapped_column(Boolean, default=False)


class Reaction(Base):
    __tablename__ = "reactions"

    message_id: Mapped[str] = mapped_column(ForeignKey("messages.id", ondelete="CASCADE"), primary_key=True)
    member_id: Mapped[str] = mapped_column(ForeignKey("members.id"), primary_key=True)
    emoji: Mapped[str] = mapped_column(String(16), primary_key=True)


class Mention(Base):
    __tablename__ = "mentions"

    message_id: Mapped[str] = mapped_column(ForeignKey("messages.id", ondelete="CASCADE"), primary_key=True)
    member_id: Mapped[str] = mapped_column(ForeignKey("members.id"), primary_key=True)


class Attachment(Base):
    __tablename__ = "attachments"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    message_id: Mapped[Optional[str]] = mapped_column(ForeignKey("messages.id", ondelete="CASCADE"), nullable=True, index=True)
    uploader_id: Mapped[str] = mapped_column(ForeignKey("members.id"))
    filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(120))
    size: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PresenceLog(Base):
    """Dernière activité connue (pour « vu il y a 20 min »)."""

    __tablename__ = "presence_log"

    member_id: Mapped[str] = mapped_column(ForeignKey("members.id"), primary_key=True)
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True))
