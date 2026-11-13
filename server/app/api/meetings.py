"""Réunions : planifier, inviter, lien visio, réponses, rappels, statut « En réunion », compte rendu."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Set

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import current_member
from app.api.chat import channel_or_404, emit_message, set_read
from app.db import SessionLocal, get_session
from app.domain.models import Channel, Meeting, MeetingAttendee, Member, Message
from app.domain.visio import VisioUnavailable, google_meet_ready, make_link
from app.realtime import hub, now

router = APIRouter(prefix="/api/meetings", tags=["meetings"])
RESPONSES = {"yes", "maybe", "no"}


class MeetingIn(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    description: str = Field(default="", max_length=4000)
    start_at: datetime
    end_at: datetime
    attendee_ids: List[str] = Field(default_factory=list, max_length=50)
    link_kind: str = "jitsi"
    channel_id: Optional[str] = None
    reminder_minutes: int = Field(default=10, ge=0, le=1440)


class MeetingPatch(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=160)
    description: Optional[str] = Field(default=None, max_length=4000)
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    attendee_ids: Optional[List[str]] = None
    reminder_minutes: Optional[int] = Field(default=None, ge=0, le=1440)


class RespondIn(BaseModel):
    response: str


class NotesIn(BaseModel):
    notes: str = Field(max_length=50000)


async def serialize(session: AsyncSession, meetings: List[Meeting]) -> List[dict]:
    if not meetings:
        return []
    rows = (await session.scalars(select(MeetingAttendee).where(
        MeetingAttendee.meeting_id.in_([m.id for m in meetings])))).all()
    by: dict = {}
    for r in rows:
        by.setdefault(r.meeting_id, []).append({"member_id": r.member_id, "response": r.response,
                                                "joined": r.joined_at is not None})
    return [{
        "id": m.id, "title": m.title, "description": m.description, "start_at": m.start_at, "end_at": m.end_at,
        "organizer_id": m.organizer_id, "link_kind": m.link_kind, "link": m.link, "channel_id": m.channel_id,
        "reminder_minutes": m.reminder_minutes, "cancelled": m.cancelled, "notes": m.notes,
        "notes_by": m.notes_by, "notes_at": m.notes_at, "attendees": by.get(m.id, []),
    } for m in meetings]


async def one(session: AsyncSession, meeting_id: str) -> Meeting:
    m = await session.get(Meeting, meeting_id)
    if m is None:
        raise HTTPException(404, "Réunion introuvable")
    return m


async def broadcast_meeting(session: AsyncSession, m: Meeting, kind: str = "meeting.updated") -> dict:
    data = (await serialize(session, [m]))[0]
    await hub.broadcast({"type": kind, "meeting": data})
    return data


async def set_attendees(session: AsyncSession, m: Meeting, ids: List[str]) -> Set[str]:
    wanted = set(ids) | {m.organizer_id}
    valid = set((await session.scalars(select(Member.id).where(Member.id.in_(wanted)))).all())
    if valid != wanted:
        raise HTTPException(400, "Membres inconnus")
    current = {r.member_id: r for r in (await session.scalars(
        select(MeetingAttendee).where(MeetingAttendee.meeting_id == m.id))).all()}
    for mid in set(current) - wanted:
        await session.delete(current[mid])
    added = wanted - set(current)
    for mid in added:
        session.add(MeetingAttendee(meeting_id=m.id, member_id=mid, response="yes" if mid == m.organizer_id else "pending"))
    return added - {m.organizer_id}


async def post_in_channel(session: AsyncSession, channel_id: str, author: Member, body: str) -> None:
    ch = await channel_or_404(session, channel_id, author)
    msg = Message(channel_id=ch.id, author_id=author.id, body=body, created_at=now())
    session.add(msg)
    await session.flush()
    await set_read(session, ch.id, author.id, msg.created_at)
    await session.commit()
    await emit_message(session, ch, msg, "message.new")


def check_times(start: datetime, end: datetime) -> None:
    if end <= start:
        raise HTTPException(400, "La fin doit être après le début")
    if end - start > timedelta(hours=12):
        raise HTTPException(400, "Une réunion dure 12 h au plus")


# ---------- routes ----------
@router.get("/config")
async def visio_config(_me: Member = Depends(current_member)):
    return {"google_meet": google_meet_ready(), "jitsi": True}


@router.get("")
async def list_meetings(start: datetime, end: datetime, _me: Member = Depends(current_member),
                        session: AsyncSession = Depends(get_session)):
    """Toutes les réunions de l'équipe sur la période (l'agenda est partagé)."""
    rows = (await session.scalars(select(Meeting).where(
        Meeting.start_at < end, Meeting.end_at > start).order_by(Meeting.start_at))).all()
    return await serialize(session, list(rows))


@router.get("/upcoming")
async def upcoming(me: Member = Depends(current_member), session: AsyncSession = Depends(get_session)):
    mine = select(MeetingAttendee.meeting_id).where(MeetingAttendee.member_id == me.id, MeetingAttendee.response != "no")
    rows = (await session.scalars(select(Meeting).where(
        Meeting.id.in_(mine), Meeting.cancelled.is_(False), Meeting.end_at > now())
        .order_by(Meeting.start_at).limit(5))).all()
    return await serialize(session, list(rows))


@router.get("/{meeting_id}")
async def get_meeting(meeting_id: str, _me: Member = Depends(current_member), session: AsyncSession = Depends(get_session)):
    return (await serialize(session, [await one(session, meeting_id)]))[0]


@router.post("", status_code=201)
async def create(body: MeetingIn, me: Member = Depends(current_member), session: AsyncSession = Depends(get_session)):
    check_times(body.start_at, body.end_at)
    if body.channel_id:
        await channel_or_404(session, body.channel_id, me)
    try:
        link = make_link(body.link_kind, body.title)
    except VisioUnavailable as e:
        raise HTTPException(400, str(e))
    m = Meeting(title=body.title.strip(), description=body.description.strip(), start_at=body.start_at,
                end_at=body.end_at, organizer_id=me.id, link_kind=body.link_kind, link=link,
                channel_id=body.channel_id, reminder_minutes=body.reminder_minutes)
    session.add(m)
    await session.flush()
    invited = await set_attendees(session, m, body.attendee_ids)
    await session.commit()
    data = await broadcast_meeting(session, m, "meeting.created")
    if invited:
        await hub.broadcast({"type": "meeting.invited", "meeting": data, "by": me.id}, to=invited)
    if body.channel_id:
        await post_in_channel(session, body.channel_id, me, f"<meeting:{m.id}>")
    await refresh_presence()
    return data


@router.patch("/{meeting_id}")
async def update(meeting_id: str, body: MeetingPatch, me: Member = Depends(current_member),
                 session: AsyncSession = Depends(get_session)):
    m = await one(session, meeting_id)
    if m.organizer_id != me.id:
        raise HTTPException(403, "Seul l'organisateur peut modifier la réunion")
    data = body.model_dump(exclude_unset=True)
    attendees = data.pop("attendee_ids", None)
    for k, v in data.items():
        setattr(m, k, v.strip() if isinstance(v, str) else v)
    check_times(m.start_at, m.end_at)
    if "start_at" in data or "reminder_minutes" in data:
        m.reminded = False
    invited: Set[str] = set()
    if attendees is not None:
        invited = await set_attendees(session, m, attendees)
    await session.commit()
    out = await broadcast_meeting(session, m)
    if invited:
        await hub.broadcast({"type": "meeting.invited", "meeting": out, "by": me.id}, to=invited)
    await refresh_presence()
    return out


@router.post("/{meeting_id}/cancel")
async def cancel(meeting_id: str, me: Member = Depends(current_member), session: AsyncSession = Depends(get_session)):
    m = await one(session, meeting_id)
    if m.organizer_id != me.id:
        raise HTTPException(403, "Seul l'organisateur peut annuler la réunion")
    m.cancelled = True
    await session.commit()
    await refresh_presence()
    return await broadcast_meeting(session, m)


@router.post("/{meeting_id}/respond")
async def respond(meeting_id: str, body: RespondIn, me: Member = Depends(current_member),
                  session: AsyncSession = Depends(get_session)):
    if body.response not in RESPONSES:
        raise HTTPException(400, "Réponse inconnue")
    m = await one(session, meeting_id)
    row = await session.get(MeetingAttendee, (m.id, me.id))
    if row is None:  # quelqu'un de l'équipe peut se joindre de lui-même
        row = MeetingAttendee(meeting_id=m.id, member_id=me.id)
        session.add(row)
    row.response = body.response
    await session.commit()
    await refresh_presence()
    return await broadcast_meeting(session, m)


@router.post("/{meeting_id}/join")
async def join(meeting_id: str, me: Member = Depends(current_member), session: AsyncSession = Depends(get_session)):
    """Clic sur « Rejoindre » : on passe « En réunion » tout de suite."""
    m = await one(session, meeting_id)
    if m.cancelled:
        raise HTTPException(400, "Réunion annulée")
    row = await session.get(MeetingAttendee, (m.id, me.id))
    if row is None:
        row = MeetingAttendee(meeting_id=m.id, member_id=me.id, response="yes")
        session.add(row)
    row.joined_at = now()
    await session.commit()
    await refresh_presence()
    await broadcast_meeting(session, m)
    return {"link": m.link}


@router.put("/{meeting_id}/notes")
async def save_notes(meeting_id: str, body: NotesIn, me: Member = Depends(current_member),
                     session: AsyncSession = Depends(get_session)):
    m = await one(session, meeting_id)
    m.notes, m.notes_by, m.notes_at = body.notes, me.id, now()
    await session.commit()
    return await broadcast_meeting(session, m)


@router.post("/{meeting_id}/notes/publish")
async def publish_notes(meeting_id: str, me: Member = Depends(current_member), session: AsyncSession = Depends(get_session)):
    m = await one(session, meeting_id)
    if not m.notes.strip():
        raise HTTPException(400, "Le compte rendu est vide")
    target = m.channel_id or "general"
    await post_in_channel(session, target, me, f"📝 Compte rendu de « {m.title} »\n\n{m.notes.strip()}")
    return {"channel_id": target}


# ---------- statut « En réunion » et rappels ----------
async def members_in_meeting(session: AsyncSession, at: datetime) -> Set[str]:
    q = select(MeetingAttendee.member_id).join(Meeting).where(
        Meeting.cancelled.is_(False), Meeting.end_at > at,
        or_(and_(Meeting.start_at <= at, MeetingAttendee.response == "yes"),
            and_(MeetingAttendee.joined_at.isnot(None), Meeting.start_at <= at + timedelta(minutes=15))),
    )
    return set((await session.scalars(q)).all())


async def refresh_presence(at: Optional[datetime] = None) -> None:
    async with SessionLocal() as s:
        current = await members_in_meeting(s, at or now())
    changed = current ^ hub.in_meeting
    hub.in_meeting = current
    for mid in changed:
        await hub.broadcast({"type": "presence", **hub.snapshot(mid)})


async def send_reminders(at: Optional[datetime] = None) -> List[str]:
    at = at or now()
    sent = []
    async with SessionLocal() as s:
        due = (await s.scalars(select(Meeting).where(
            Meeting.cancelled.is_(False), Meeting.reminded.is_(False), Meeting.start_at > at - timedelta(minutes=1),
            Meeting.start_at <= at + timedelta(minutes=60 * 24)))).all()
        for m in due:
            if m.start_at - timedelta(minutes=m.reminder_minutes) > at:
                continue
            m.reminded = True
            people = set((await s.scalars(select(MeetingAttendee.member_id).where(
                MeetingAttendee.meeting_id == m.id, MeetingAttendee.response != "no"))).all())
            data = (await serialize(s, [m]))[0]
            await hub.broadcast({"type": "meeting.reminder", "meeting": data}, to=people)
            sent.append(m.id)
        await s.commit()
    return sent


async def scheduler() -> None:
    """Tourne en fond : toutes les 20 s, rappels et statut « En réunion »."""
    while True:
        try:
            await send_reminders()
            await refresh_presence()
            from app.api.timesheet import send_time_asks
            await send_time_asks()
        except Exception as e:  # on ne laisse jamais tomber la boucle
            print("planificateur :", e)
        await asyncio.sleep(20)
