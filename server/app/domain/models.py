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


class Meeting(Base):
    """Une réunion de l'agenda HQ, avec son lien visio et son compte rendu."""

    __tablename__ = "meetings"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    title: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(Text, default="")
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    organizer_id: Mapped[str] = mapped_column(ForeignKey("members.id"))
    link_kind: Mapped[str] = mapped_column(String(10), default="jitsi")  # jitsi | meet | none
    link: Mapped[str] = mapped_column(String(300), default="")
    channel_id: Mapped[Optional[str]] = mapped_column(ForeignKey("channels.id"), nullable=True)
    reminder_minutes: Mapped[int] = mapped_column(Integer, default=10)
    reminded: Mapped[bool] = mapped_column(Boolean, default=False)
    cancelled: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str] = mapped_column(Text, default="")
    notes_by: Mapped[Optional[str]] = mapped_column(ForeignKey("members.id"), nullable=True)
    notes_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MeetingAttendee(Base):
    __tablename__ = "meeting_attendees"

    meeting_id: Mapped[str] = mapped_column(ForeignKey("meetings.id", ondelete="CASCADE"), primary_key=True)
    member_id: Mapped[str] = mapped_column(ForeignKey("members.id"), primary_key=True)
    response: Mapped[str] = mapped_column(String(10), default="pending")  # pending | yes | maybe | no
    joined_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class Position(Base):
    """Un poste de l'organisation (fiches de poste NYUMAN, 12/11/2026)."""

    __tablename__ = "positions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)  # numéro du poste (1 à 12)
    title: Mapped[str] = mapped_column(String(120))
    department: Mapped[str] = mapped_column(String(60))
    reports_to: Mapped[Optional[int]] = mapped_column(ForeignKey("positions.id"), nullable=True)
    mission: Mapped[str] = mapped_column(String(300), default="")
    hours: Mapped[str] = mapped_column(String(20), default="")


class PositionHolder(Base):
    """Qui tient le poste (humain) ou l'appuie (agent)."""

    __tablename__ = "position_holders"

    position_id: Mapped[int] = mapped_column(ForeignKey("positions.id", ondelete="CASCADE"), primary_key=True)
    member_id: Mapped[str] = mapped_column(ForeignKey("members.id"), primary_key=True)
    kind: Mapped[str] = mapped_column(String(10), default="holder")  # holder | support


class AgentToken(Base):
    """Clé d'accès d'un agent (on ne garde que son empreinte, jamais la clé)."""

    __tablename__ = "agent_tokens"

    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    member_id: Mapped[str] = mapped_column(ForeignKey("members.id"), index=True)
    created_by: Mapped[str] = mapped_column(ForeignKey("members.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
