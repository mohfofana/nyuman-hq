"""Messagerie : canaux, messages privés, fils, réactions, mentions, non-lus, recherche, activité."""
from __future__ import annotations

import re
from datetime import datetime
from typing import Dict, List, Optional, Set

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import and_, func, or_, select
from sqlalchemy import text as sql_text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import current_member
from app.db import get_session
from app.domain.models import Attachment, Channel, ChannelMember, Member, Mention, Message, Reaction
from app.realtime import hub, now

router = APIRouter(prefix="/api", tags=["chat"])
MENTION_RE = re.compile(r"<@([a-z0-9_-]{1,40})>")
MAX_BODY = 8000


# ---------- schémas ----------
class ChannelIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    topic: str = Field(default="", max_length=200)


class DmIn(BaseModel):
    member_ids: List[str] = Field(min_length=1, max_length=12)


class MessageIn(BaseModel):
    body: str = Field(default="", max_length=MAX_BODY)
    parent_id: Optional[str] = None
    attachment_ids: List[str] = Field(default_factory=list, max_length=10)


class MessageEdit(BaseModel):
    body: str = Field(min_length=1, max_length=MAX_BODY)


class ReactionIn(BaseModel):
    emoji: str = Field(min_length=1, max_length=16)


# ---------- accès ----------
async def channel_or_404(session: AsyncSession, channel_id: str, me: Member) -> Channel:
    ch = await session.get(Channel, channel_id)
    if ch is None:
        raise HTTPException(404, "Discussion introuvable")
    if ch.kind == "dm":
        row = await session.get(ChannelMember, (ch.id, me.id))
        if row is None:
            raise HTTPException(404, "Discussion introuvable")
    return ch


async def audience(session: AsyncSession, ch: Channel) -> Optional[Set[str]]:
    """Qui reçoit les événements : tout le monde pour un canal, les membres pour un privé."""
    if ch.kind == "channel":
        return None
    rows = await session.scalars(select(ChannelMember.member_id).where(ChannelMember.channel_id == ch.id))
    return set(rows.all())


async def accessible_channel_ids(session: AsyncSession, me: Member) -> List[str]:
    q = select(Channel.id).where(
        or_(Channel.kind == "channel",
            Channel.id.in_(select(ChannelMember.channel_id).where(ChannelMember.member_id == me.id)))
    )
    return list((await session.scalars(q)).all())


async def set_read(session: AsyncSession, channel_id: str, member_id: str, at) -> None:
    """Marque comme lu, sans conflit si deux demandes arrivent en même temps."""
    stmt = pg_insert(ChannelMember).values(channel_id=channel_id, member_id=member_id, last_read_at=at)
    await session.execute(stmt.on_conflict_do_update(
        index_elements=[ChannelMember.channel_id, ChannelMember.member_id], set_={"last_read_at": at}))


# ---------- sérialisation ----------
async def serialize(session: AsyncSession, msgs: List[Message]) -> List[dict]:
    if not msgs:
        return []
    ids = [m.id for m in msgs]
    reactions: Dict[str, Dict[str, List[str]]] = {}
    for r in (await session.scalars(select(Reaction).where(Reaction.message_id.in_(ids)))).all():
        reactions.setdefault(r.message_id, {}).setdefault(r.emoji, []).append(r.member_id)
    files: Dict[str, List[dict]] = {}
    for a in (await session.scalars(select(Attachment).where(Attachment.message_id.in_(ids)))).all():
        files.setdefault(a.message_id, []).append({
            "id": a.id, "filename": a.filename, "content_type": a.content_type, "size": a.size,
            "url": f"/api/uploads/{a.id}/{a.filename}",
        })
    replies: Dict[str, dict] = {}
    rows = await session.execute(
        select(Message.parent_id, func.count(), func.max(Message.created_at), func.array_agg(func.distinct(Message.author_id)))
        .where(Message.parent_id.in_(ids), Message.deleted.is_(False)).group_by(Message.parent_id)
    )
    for parent_id, count, last, authors in rows.all():
        replies[parent_id] = {"reply_count": count, "last_reply_at": last, "reply_authors": list(authors)[:5]}
    out = []
    for m in msgs:
        out.append({
            "id": m.id, "channel_id": m.channel_id, "author_id": m.author_id, "parent_id": m.parent_id,
            "body": "" if m.deleted else m.body, "deleted": m.deleted,
            "created_at": m.created_at, "edited_at": m.edited_at,
            "reactions": [{"emoji": e, "member_ids": who} for e, who in reactions.get(m.id, {}).items()],
            "attachments": [] if m.deleted else files.get(m.id, []),
            **replies.get(m.id, {"reply_count": 0, "last_reply_at": None, "reply_authors": []}),
        })
    return out


async def emit_message(session: AsyncSession, ch: Channel, msg: Message, kind: str) -> dict:
    data = (await serialize(session, [msg]))[0]
    await hub.broadcast({"type": kind, "message": data}, to=await audience(session, ch))
    if msg.parent_id:  # le compteur de réponses du message parent change
        parent = await session.get(Message, msg.parent_id)
        if parent:
            pdata = (await serialize(session, [parent]))[0]
            await hub.broadcast({"type": "message.updated", "message": pdata}, to=await audience(session, ch))
    return data


# ---------- canaux ----------
@router.get("/channels")
async def list_channels(me: Member = Depends(current_member), session: AsyncSession = Depends(get_session)):
    chans = (await session.scalars(select(Channel).where(Channel.id.in_(await accessible_channel_ids(session, me)))
                                   .order_by(Channel.kind, Channel.name))).all()
    reads = {r.channel_id: r.last_read_at for r in (await session.scalars(
        select(ChannelMember).where(ChannelMember.member_id == me.id))).all()}
    dm_members: Dict[str, List[str]] = {}
    dm_ids = [c.id for c in chans if c.kind == "dm"]
    if dm_ids:
        for r in (await session.scalars(select(ChannelMember).where(ChannelMember.channel_id.in_(dm_ids)))).all():
            dm_members.setdefault(r.channel_id, []).append(r.member_id)
    out = []
    for c in chans:
        since = reads.get(c.id) or me.created_at
        unread = await session.scalar(select(func.count()).select_from(Message).where(
            Message.channel_id == c.id, Message.author_id != me.id, Message.deleted.is_(False),
            Message.created_at > since))
        mentions = await session.scalar(select(func.count()).select_from(Mention).join(Message).where(
            Message.channel_id == c.id, Mention.member_id == me.id, Message.created_at > since))
        last_at = await session.scalar(select(func.max(Message.created_at)).where(Message.channel_id == c.id))
        out.append({
            "id": c.id, "kind": c.kind, "name": c.name, "topic": c.topic,
            "member_ids": sorted(dm_members.get(c.id, [])),
            "unread": unread or 0, "mentions": mentions or 0, "last_message_at": last_at,
        })
    return out


@router.post("/channels", status_code=201)
async def create_channel(body: ChannelIn, me: Member = Depends(current_member), session: AsyncSession = Depends(get_session)):
    name = body.name.strip().lstrip("#").lower()
    if await session.scalar(select(Channel).where(Channel.kind == "channel", Channel.name == name)):
        raise HTTPException(409, "Un canal porte déjà ce nom")
    ch = Channel(kind="channel", name=name, topic=body.topic.strip(), created_by=me.id)
    session.add(ch)
    await session.commit()
    await hub.broadcast({"type": "channel.created", "channel_id": ch.id})
    return {"id": ch.id}


@router.post("/dms", status_code=200)
async def open_dm(body: DmIn, me: Member = Depends(current_member), session: AsyncSession = Depends(get_session)):
    wanted = set(body.member_ids) | {me.id}
    found = (await session.scalars(select(Member.id).where(Member.id.in_(wanted)))).all()
    if len(found) != len(wanted) or len(wanted) < 2:
        raise HTTPException(400, "Membres inconnus")
    # Un seul à la fois pour ce groupe de personnes (deux clics rapprochés ne créent pas deux discussions).
    await session.execute(sql_text("select pg_advisory_xact_lock(hashtext(:k))"), {"k": "dm:" + ",".join(sorted(wanted))})
    # cherche une discussion privée avec exactement ces membres
    candidates = (await session.scalars(
        select(ChannelMember.channel_id).join(Channel).where(Channel.kind == "dm", ChannelMember.member_id == me.id))).all()
    for cid in candidates:
        ids = set((await session.scalars(select(ChannelMember.member_id).where(ChannelMember.channel_id == cid))).all())
        if ids == wanted:
            return {"id": cid}
    ch = Channel(kind="dm", created_by=me.id)
    session.add(ch)
    await session.flush()
    for mid in wanted:
        session.add(ChannelMember(channel_id=ch.id, member_id=mid, last_read_at=now() if mid == me.id else None))
    await session.commit()
    await hub.broadcast({"type": "channel.created", "channel_id": ch.id}, to=wanted)
    return {"id": ch.id}


@router.post("/channels/{channel_id}/read", status_code=204)
async def mark_read(channel_id: str, me: Member = Depends(current_member), session: AsyncSession = Depends(get_session)):
    await channel_or_404(session, channel_id, me)
    await set_read(session, channel_id, me.id, now())
    await session.commit()


# ---------- messages ----------
@router.get("/channels/{channel_id}/messages")
async def list_messages(channel_id: str, before: Optional[datetime] = None, limit: int = 50,
                        me: Member = Depends(current_member), session: AsyncSession = Depends(get_session)):
    await channel_or_404(session, channel_id, me)
    q = select(Message).where(Message.channel_id == channel_id, Message.parent_id.is_(None))
    if before:
        q = q.where(Message.created_at < before)
    msgs = list((await session.scalars(q.order_by(Message.created_at.desc()).limit(min(limit, 100)))).all())
    msgs.reverse()
    return await serialize(session, msgs)


@router.get("/messages/{message_id}/thread")
async def thread(message_id: str, me: Member = Depends(current_member), session: AsyncSession = Depends(get_session)):
    root = await session.get(Message, message_id)
    if root is None:
        raise HTTPException(404)
    await channel_or_404(session, root.channel_id, me)
    replies = (await session.scalars(select(Message).where(Message.parent_id == root.id).order_by(Message.created_at))).all()
    return {"root": (await serialize(session, [root]))[0], "replies": await serialize(session, list(replies))}


@router.post("/channels/{channel_id}/messages", status_code=201)
async def post_message(channel_id: str, body: MessageIn, me: Member = Depends(current_member),
                       session: AsyncSession = Depends(get_session)):
    ch = await channel_or_404(session, channel_id, me)
    text = body.body.strip()
    if not text and not body.attachment_ids:
        raise HTTPException(400, "Message vide")
    if body.parent_id:
        parent = await session.get(Message, body.parent_id)
        if parent is None or parent.channel_id != ch.id or parent.parent_id is not None:
            raise HTTPException(400, "Fil introuvable")
    msg = Message(channel_id=ch.id, author_id=me.id, parent_id=body.parent_id, body=text, created_at=now())
    session.add(msg)
    await session.flush()
    if body.attachment_ids:
        files = (await session.scalars(select(Attachment).where(
            Attachment.id.in_(body.attachment_ids), Attachment.uploader_id == me.id, Attachment.message_id.is_(None)))).all()
        for f in files:
            f.message_id = msg.id
    mentioned = set(MENTION_RE.findall(text))
    if mentioned:
        valid = set((await session.scalars(select(Member.id).where(Member.id.in_(mentioned)))).all())
        for mid in valid - {me.id}:
            session.add(Mention(message_id=msg.id, member_id=mid))
    # celui qui écrit a forcément tout lu
    await set_read(session, ch.id, me.id, msg.created_at)
    await session.commit()
    hub.touch(me.id)
    return await emit_message(session, ch, msg, "message.new")


async def own_message(session: AsyncSession, message_id: str, me: Member) -> Message:
    msg = await session.get(Message, message_id)
    if msg is None or msg.deleted:
        raise HTTPException(404)
    if msg.author_id != me.id:
        raise HTTPException(403, "Seul l'auteur peut faire ça")
    return msg


@router.patch("/messages/{message_id}")
async def edit_message(message_id: str, body: MessageEdit, me: Member = Depends(current_member),
                       session: AsyncSession = Depends(get_session)):
    msg = await own_message(session, message_id, me)
    msg.body, msg.edited_at = body.body.strip(), now()
    await session.commit()
    ch = await session.get(Channel, msg.channel_id)
    return await emit_message(session, ch, msg, "message.updated")


@router.delete("/messages/{message_id}")
async def delete_message(message_id: str, me: Member = Depends(current_member), session: AsyncSession = Depends(get_session)):
    msg = await own_message(session, message_id, me)
    msg.deleted = True
    await session.commit()
    ch = await session.get(Channel, msg.channel_id)
    return await emit_message(session, ch, msg, "message.updated")


@router.post("/messages/{message_id}/reactions")
async def toggle_reaction(message_id: str, body: ReactionIn, me: Member = Depends(current_member),
                          session: AsyncSession = Depends(get_session)):
    msg = await session.get(Message, message_id)
    if msg is None or msg.deleted:
        raise HTTPException(404)
    ch = await channel_or_404(session, msg.channel_id, me)
    existing = await session.get(Reaction, (msg.id, me.id, body.emoji))
    if existing:
        await session.delete(existing)
    else:
        session.add(Reaction(message_id=msg.id, member_id=me.id, emoji=body.emoji))
    await session.commit()
    return await emit_message(session, ch, msg, "message.updated")


# ---------- recherche et activité ----------
@router.get("/search")
async def search(q: str, me: Member = Depends(current_member), session: AsyncSession = Depends(get_session)):
    q = q.strip()
    if len(q) < 2:
        return []
    pattern = "%" + q.replace("%", r"\%").replace("_", r"\_") + "%"
    msgs = (await session.scalars(select(Message).where(
        Message.channel_id.in_(await accessible_channel_ids(session, me)),
        Message.deleted.is_(False), Message.body.ilike(pattern)).order_by(Message.created_at.desc()).limit(30))).all()
    return await serialize(session, list(msgs))


@router.get("/activity")
async def activity(me: Member = Depends(current_member), session: AsyncSession = Depends(get_session)):
    """Ce qui me concerne : mentions, et réponses dans les fils où j'ai écrit."""
    my_threads = select(Message.id).where(Message.author_id == me.id, Message.parent_id.is_(None))
    replied = select(Message.parent_id).where(Message.author_id == me.id, Message.parent_id.isnot(None))
    q = select(Message).where(
        Message.deleted.is_(False), Message.author_id != me.id,
        Message.channel_id.in_(await accessible_channel_ids(session, me)),
        or_(Message.id.in_(select(Mention.message_id).where(Mention.member_id == me.id)),
            and_(Message.parent_id.isnot(None), or_(Message.parent_id.in_(my_threads), Message.parent_id.in_(replied)))),
    ).order_by(Message.created_at.desc()).limit(40)
    msgs = list((await session.scalars(q)).all())
    mention_ids = set((await session.scalars(select(Mention.message_id).where(
        Mention.member_id == me.id, Mention.message_id.in_([m.id for m in msgs])))).all())
    data = await serialize(session, msgs)
    return [{"kind": "mention" if d["id"] in mention_ids else "reply", "message": d} for d in data]
