from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Setting(Base):
    """Petits réglages que HQ se donne à lui-même. Sert surtout à la clé qui signe les sessions :
    elle est fabriquée au hasard au premier démarrage et gardée ici — personne n'a à la manipuler."""

    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(40), primary_key=True)
    value: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


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
    # Suivi du temps (façon Gryzzly) : jours travaillés (1 = lundi … 7 = dimanche) et heure de la question du soir.
    work_days: Mapped[str] = mapped_column(String(20), default="1,2,3,4,5", server_default="1,2,3,4,5")
    ask_hour: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=19, server_default="19")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


def _uuid() -> str:
    import uuid

    return uuid.uuid4().hex


class MemberEmail(Base):
    """Une adresse Google qui ouvre HQ. Chacun peut en avoir plusieurs : la pro et la perso."""

    __tablename__ = "member_emails"

    email: Mapped[str] = mapped_column(String(160), primary_key=True)  # toujours en minuscules
    member_id: Mapped[str] = mapped_column(ForeignKey("members.id", ondelete="CASCADE"), index=True)
    added_by: Mapped[Optional[str]] = mapped_column(ForeignKey("members.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Invite(Base):
    """Lien d'invitation : la personne se connecte avec Google, et son adresse se range sur sa fiche.

    Un seul usage, 7 jours. HQ n'en garde que l'empreinte : le lien complet n'existe qu'une fois,
    au moment où le responsable le copie.
    """

    __tablename__ = "invites"

    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    member_id: Mapped[str] = mapped_column(ForeignKey("members.id", ondelete="CASCADE"), index=True)
    created_by: Mapped[str] = mapped_column(ForeignKey("members.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class JoinRequest(Base):
    """Quelqu'un arrive sur HQ avec une adresse inconnue, dit qui il est, et attend qu'un responsable confirme.

    Google a déjà prouvé que l'adresse est bien la sienne ; le responsable confirme seulement que
    c'est bien la bonne personne.
    """

    __tablename__ = "join_requests"

    email: Mapped[str] = mapped_column(String(160), primary_key=True)  # minuscules
    member_id: Mapped[str] = mapped_column(ForeignKey("members.id", ondelete="CASCADE"), index=True)
    name_seen: Mapped[str] = mapped_column(String(120), default="")  # le nom tel que Google le donne
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class LoginLink(Base):
    """Lien de connexion envoyé par e-mail : valable 20 minutes, une seule fois.
    HQ n'en garde que l'empreinte ; le lien complet n'existe que dans le message reçu."""

    __tablename__ = "login_links"

    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    email: Mapped[str] = mapped_column(String(160), index=True)  # minuscules
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Channel(Base):
    """Un canal d'équipe ou une discussion privée (dm).

    Un canal est ouvert à toute l'équipe, ou fermé : dans ce cas seules les personnes et les agents
    qui en font partie le voient, comme un groupe WhatsApp.
    """

    __tablename__ = "channels"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    kind: Mapped[str] = mapped_column(String(10))  # "channel" | "dm"
    name: Mapped[str] = mapped_column(String(80), default="")
    topic: Mapped[str] = mapped_column(String(200), default="")
    private: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    archived: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    created_by: Mapped[Optional[str]] = mapped_column(ForeignKey("members.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ChannelMember(Base):
    """Le lien entre une personne (ou un agent) et un canal.

    `joined` distingue « il fait partie du canal » de « il l'a seulement lu » : un canal ouvert
    crée une ligne dès la première lecture, et ça ne doit pas en faire un participant.
    """

    __tablename__ = "channel_members"

    channel_id: Mapped[str] = mapped_column(ForeignKey("channels.id", ondelete="CASCADE"), primary_key=True)
    member_id: Mapped[str] = mapped_column(ForeignKey("members.id"), primary_key=True)
    joined: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
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


class Project(Base):
    """Un projet (façon Notion) : ses pages et ses tâches."""

    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(120))
    icon: Mapped[str] = mapped_column(String(16), default="📁")
    description: Mapped[str] = mapped_column(Text, default="")
    department: Mapped[str] = mapped_column(String(60), default="")
    owner_id: Mapped[Optional[str]] = mapped_column(ForeignKey("members.id"), nullable=True)
    created_by: Mapped[str] = mapped_column(ForeignKey("members.id"))
    archived: Mapped[bool] = mapped_column(Boolean, default=False)
    hours_budget: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # budget d'heures, facultatif
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Page(Base):
    __tablename__ = "pages"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    parent_id: Mapped[Optional[str]] = mapped_column(ForeignKey("pages.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(200), default="")
    icon: Mapped[str] = mapped_column(String(16), default="📄")
    content: Mapped[str] = mapped_column(Text, default="")  # document de l'éditeur (JSON)
    text: Mapped[str] = mapped_column(Text, default="")  # texte brut, pour la recherche et les agents
    position: Mapped[float] = mapped_column(Float, default=0)
    archived: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[str] = mapped_column(ForeignKey("members.id"))
    updated_by: Mapped[Optional[str]] = mapped_column(ForeignKey("members.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(300))
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(12), default="todo")  # todo | doing | review | done
    priority: Mapped[str] = mapped_column(String(8), default="normal")  # low | normal | high
    assignee_id: Mapped[Optional[str]] = mapped_column(ForeignKey("members.id"), nullable=True, index=True)
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    page_id: Mapped[Optional[str]] = mapped_column(ForeignKey("pages.id"), nullable=True)
    position: Mapped[float] = mapped_column(Float, default=0)
    archived: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[str] = mapped_column(ForeignKey("members.id"))
    updated_by: Mapped[Optional[str]] = mapped_column(ForeignKey("members.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class AgentRun(Base):
    """Un réveil d'agent : pourquoi, quand, combien de temps, combien ça a coûté."""

    __tablename__ = "agent_runs"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    agent_id: Mapped[str] = mapped_column(ForeignKey("members.id"), index=True)
    trigger_message_id: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    channel_id: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    triggered_by: Mapped[Optional[str]] = mapped_column(ForeignKey("members.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(12), default="queued")  # queued | running | done | failed | capped
    model: Mapped[str] = mapped_column(String(40), default="")
    cost_usd: Mapped[float] = mapped_column(Float, default=0)
    duration_s: Mapped[float] = mapped_column(Float, default=0)
    error: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class TimeEntry(Base):
    """Temps déclaré par la personne elle-même (jamais mesuré) : un jour, un projet, éventuellement une tâche."""

    __tablename__ = "time_entries"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    member_id: Mapped[str] = mapped_column(ForeignKey("members.id"), index=True)
    day: Mapped[date] = mapped_column(Date, index=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    task_id: Mapped[Optional[str]] = mapped_column(ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True)
    minutes: Mapped[int] = mapped_column(Integer)
    note: Mapped[str] = mapped_column(String(300), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TimeAsk(Base):
    """La question du soir de Maeve : une par personne et par jour travaillé."""

    __tablename__ = "time_asks"

    member_id: Mapped[str] = mapped_column(ForeignKey("members.id"), primary_key=True)
    day: Mapped[date] = mapped_column(Date, primary_key=True)
    state: Mapped[str] = mapped_column(String(10), default="asked")  # asked | answered | off
    message_id: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)


class TrackItem(Base):
    """Une ligne de suivi propre à un poste : un salon à amener à sa 1re réservation, une échéance, une dépense à valider."""

    __tablename__ = "track_items"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    kind: Mapped[str] = mapped_column(String(16), index=True)  # salon | echeance | depense
    title: Mapped[str] = mapped_column(String(200))
    stage: Mapped[str] = mapped_column(String(30))
    owner_id: Mapped[Optional[str]] = mapped_column(ForeignKey("members.id"), nullable=True)
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    amount: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    currency: Mapped[str] = mapped_column(String(6), default="FCFA")
    contact: Mapped[str] = mapped_column(String(160), default="")
    note: Mapped[str] = mapped_column(Text, default="")
    archived: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[str] = mapped_column(ForeignKey("members.id"))
    decided_by: Mapped[Optional[str]] = mapped_column(ForeignKey("members.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Proposal(Base):
    """Salle du conseil : une proposition (texte, chiffres, avis de Koffi) soumise au vote des heads."""

    __tablename__ = "proposals"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text, default="")
    figures: Mapped[str] = mapped_column(Text, default="")
    author_id: Mapped[str] = mapped_column(ForeignKey("members.id"))
    status: Mapped[str] = mapped_column(String(12), default="open")  # open | adopted | rejected | withdrawn
    deadline: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    opinion: Mapped[str] = mapped_column(Text, default="")  # avis du contradicteur
    opinion_by: Mapped[Optional[str]] = mapped_column(ForeignKey("members.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class Vote(Base):
    __tablename__ = "votes"

    proposal_id: Mapped[str] = mapped_column(ForeignKey("proposals.id", ondelete="CASCADE"), primary_key=True)
    member_id: Mapped[str] = mapped_column(ForeignKey("members.id"), primary_key=True)
    choice: Mapped[str] = mapped_column(String(12))  # pour | contre | abstention
    comment: Mapped[str] = mapped_column(String(500), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
