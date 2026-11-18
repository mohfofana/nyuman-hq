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
from app.config import settings
from app.db import get_session
from app.domain.models import Attachment, Channel, ChannelMember, Member, Mention, Message, Reaction
from app.realtime import hub, now

router = APIRouter(prefix="/api", tags=["chat"])
MENTION_RE = re.compile(r"<@([a-z0-9_-]{1,40})>")
EVERYONE = "tous"


def manages_channels(me: Member) -> bool:
    """Créer, modifier, supprimer un canal : réservé aux personnes désignées (Mohamed, Abraham)."""
    return me.kind == "human" and me.id in {a.strip() for a in settings.channel_admins.split(",") if a.strip()}


def require_channel_admin(me: Member) -> None:
    if not manages_channels(me):
        raise HTTPException(403, "Seuls Mohamed et Abraham gèrent les canaux")  # @tous : prévient tous les humains du canal, jamais les agents
MAX_BODY = 8000


# ---------- schémas ----------
class ChannelIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    topic: str = Field(default="", max_length=200)
    private: bool = False
    member_ids: List[str] = Field(default_factory=list, max_length=60)


class ChannelPatch(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=80)
    topic: Optional[str] = Field(default=None, max_length=200)
    private: Optional[bool] = None


class MembersIn(BaseModel):
    member_ids: List[str] = Field(min_length=1, max_length=60)


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
    if ch.archived:
        raise HTTPException(404, "Discussion introuvable")
    if ch.kind == "dm" or ch.private:
        row = await session.get(ChannelMember, (ch.id, me.id))
        if row is None or not row.joined:
            raise HTTPException(404, "Discussion introuvable")
    return ch


async def audience(session: AsyncSession, ch: Channel) -> Optional[Set[str]]:
    """Qui reçoit les événements : tout le monde pour un canal, les membres pour un privé."""
    if ch.kind == "channel" and not ch.private:
        return None
    rows = await session.scalars(select(ChannelMember.member_id).where(
        ChannelMember.channel_id == ch.id, ChannelMember.joined.is_(True)))
    return set(rows.all())


async def accessible_channel_ids(session: AsyncSession, me: Member) -> List[str]:
    """Les canaux ouverts, plus ceux (fermés ou privés) dont je fais vraiment partie."""
    mine = select(ChannelMember.channel_id).where(
        ChannelMember.member_id == me.id, ChannelMember.joined.is_(True))
    q = select(Channel.id).where(
        Channel.archived.is_(False),
        or_(and_(Channel.kind == "channel", Channel.private.is_(False)), Channel.id.in_(mine)))
    return list((await session.scalars(q)).all())


async def set_read(session: AsyncSession, channel_id: str, member_id: str, at) -> None:
    """Marque comme lu, sans conflit si deux demandes arrivent en même temps.
    Lire ne rend pas participant : la ligne créée ici a joined = faux."""
    stmt = pg_insert(ChannelMember).values(channel_id=channel_id, member_id=member_id,
                                           last_read_at=at, joined=False)
    await session.execute(stmt.on_conflict_do_update(
        index_elements=[ChannelMember.channel_id, ChannelMember.member_id], set_={"last_read_at": at}))


# ---------- sérialisation ----------
async def everyone_here(session: AsyncSession, ch: Channel) -> Set[str]:
    """Les humains qui voient ce canal. Les agents sont exclus : @tous prévient l'équipe,
    il ne lance pas six agents (et six factures) d'un coup."""
    humans = set((await session.scalars(select(Member.id).where(Member.kind == "human"))).all())
    aud = await audience(session, ch)
    return humans if aud is None else humans & set(aud)


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
    # Discussions privées et canaux fermés : on donne la liste des participants.
    dm_members: Dict[str, List[str]] = {}
    avec_membres = [c.id for c in chans if c.kind == "dm" or c.private]
    if avec_membres:
        for r in (await session.scalars(select(ChannelMember).where(
                ChannelMember.channel_id.in_(avec_membres), ChannelMember.joined.is_(True)))).all():
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
            "id": c.id, "kind": c.kind, "name": c.name, "topic": c.topic, "private": c.private,
            "member_ids": sorted(dm_members.get(c.id, [])),
            "unread": unread or 0, "mentions": mentions or 0, "last_message_at": last_at,
        })
    return out


@router.post("/channels", status_code=201)
async def create_channel(body: ChannelIn, me: Member = Depends(current_member), session: AsyncSession = Depends(get_session)):
    """Crée un canal. Fermé : seules les personnes et les agents choisis le voient."""
    require_channel_admin(me)
    name = body.name.strip().lstrip("#").lower()
    if await session.scalar(select(Channel).where(Channel.kind == "channel", Channel.name == name,
                                                  Channel.archived.is_(False))):
        raise HTTPException(409, "Un canal porte déjà ce nom")
    ch = Channel(kind="channel", name=name, topic=body.topic.strip(), private=body.private, created_by=me.id)
    session.add(ch)
    await session.flush()
    if body.private:
        await add_members(session, ch, set(body.member_ids) | {me.id})
    await session.commit()
    await hub.broadcast({"type": "channel.created", "channel_id": ch.id}, to=await audience(session, ch))
    return {"id": ch.id}


async def add_members(session: AsyncSession, ch: Channel, ids: Set[str]) -> List[str]:
    """Ajoute des participants (humains ou agents). Renvoie ceux qui ont vraiment été ajoutés."""
    connus = set((await session.scalars(select(Member.id).where(Member.id.in_(ids)))).all())
    ajoutes = []
    for mid in sorted(connus):
        row = await session.get(ChannelMember, (ch.id, mid))
        if row is None:
            session.add(ChannelMember(channel_id=ch.id, member_id=mid, joined=True))
            ajoutes.append(mid)
        elif not row.joined:
            row.joined = True
            ajoutes.append(mid)
    return ajoutes


async def channel_out(session: AsyncSession, ch: Channel) -> dict:
    ids = sorted((await session.scalars(select(ChannelMember.member_id).where(
        ChannelMember.channel_id == ch.id, ChannelMember.joined.is_(True)))).all())
    return {"id": ch.id, "kind": ch.kind, "name": ch.name, "topic": ch.topic,
            "private": ch.private, "created_by": ch.created_by, "member_ids": ids}


@router.get("/channels/{channel_id}/members")
async def channel_members(channel_id: str, me: Member = Depends(current_member),
                          session: AsyncSession = Depends(get_session)):
    ch = await channel_or_404(session, channel_id, me)
    return await channel_out(session, ch)


@router.patch("/channels/{channel_id}")
async def update_channel(channel_id: str, body: ChannelPatch, me: Member = Depends(current_member),
                         session: AsyncSession = Depends(get_session)):
    """Renommer, changer le sujet, ouvrir ou fermer un canal."""
    require_channel_admin(me)
    ch = await session.get(Channel, channel_id)
    if ch is None or ch.kind != "channel" or ch.archived:
        raise HTTPException(404, "Canal introuvable")
    data = body.model_dump(exclude_unset=True)
    if "name" in data:
        name = data["name"].strip().lstrip("#").lower()
        if await session.scalar(select(Channel).where(Channel.kind == "channel", Channel.name == name,
                                                      Channel.id != ch.id, Channel.archived.is_(False))):
            raise HTTPException(409, "Un canal porte déjà ce nom")
        ch.name = name
    if "topic" in data:
        ch.topic = data["topic"].strip()
    if data.get("private") and not ch.private:
        # En fermant, on garde ceux qui y écrivaient déjà, plus celui qui ferme.
        auteurs = set((await session.scalars(select(Message.author_id).where(Message.channel_id == ch.id))).all())
        await add_members(session, ch, auteurs | {me.id})
        ch.private = True
    elif data.get("private") is False:
        ch.private = False
    await session.commit()
    await hub.broadcast({"type": "channel.updated", "channel_id": ch.id})
    return await channel_out(session, ch)


@router.post("/channels/{channel_id}/members")
async def invite_members(channel_id: str, body: MembersIn, me: Member = Depends(current_member),
                         session: AsyncSession = Depends(get_session)):
    """Ajoute des participants — des personnes comme des agents."""
    require_channel_admin(me)
    ch = await session.get(Channel, channel_id)
    if ch is None or ch.kind != "channel" or ch.archived:
        raise HTTPException(404, "Canal introuvable")
    ajoutes = await add_members(session, ch, set(body.member_ids))
    await session.commit()
    await hub.broadcast({"type": "channel.updated", "channel_id": ch.id})
    for mid in ajoutes:
        await hub.broadcast({"type": "channel.created", "channel_id": ch.id}, to={mid})
    return await channel_out(session, ch)


@router.delete("/channels/{channel_id}/members/{member_id}")
async def remove_member(channel_id: str, member_id: str, me: Member = Depends(current_member),
                        session: AsyncSession = Depends(get_session)):
    """Retire quelqu'un d'un canal. Il ne le voit plus, les messages restent."""
    require_channel_admin(me)
    ch = await session.get(Channel, channel_id)
    if ch is None or ch.kind != "channel":
        raise HTTPException(404, "Canal introuvable")
    row = await session.get(ChannelMember, (ch.id, member_id))
    if row is not None:
        row.joined = False
        await session.commit()
    await hub.broadcast({"type": "channel.updated", "channel_id": ch.id})
    await hub.broadcast({"type": "channel.removed", "channel_id": ch.id}, to={member_id})
    return await channel_out(session, ch)


@router.delete("/channels/{channel_id}", status_code=204)
async def delete_channel(channel_id: str, me: Member = Depends(current_member),
                         session: AsyncSession = Depends(get_session)):
    """Supprime un canal : il disparaît pour tout le monde. Les messages sont gardés en base."""
    require_channel_admin(me)
    ch = await session.get(Channel, channel_id)
    if ch is None or ch.kind != "channel":
        raise HTTPException(404, "Canal introuvable")
    ch.archived = True
    await session.commit()
    await hub.broadcast({"type": "channel.removed", "channel_id": ch.id})


@router.post("/dms", status_code=200)
async def open_dm(body: DmIn, me: Member = Depends(current_member), session: AsyncSession = Depends(get_session)):
    wanted = set(body.member_ids) | {me.id}
    found = (await session.scalars(select(Member.id).where(Member.id.in_(wanted)))).all()
    if len(found) != len(wanted) or len(wanted) < 2:
        raise HTTPException(400, "Membres inconnus")
    cid, created = await ensure_dm(session, wanted, me.id)
    if created:
        await hub.broadcast({"type": "channel.created", "channel_id": cid}, to=wanted)
    return {"id": cid}


async def ensure_dm(session: AsyncSession, wanted: Set[str], opener: str):
    """Retrouve ou crée la discussion privée entre exactement ces membres. Renvoie (id, créée ?)."""
    # Un seul à la fois pour ce groupe de personnes (deux clics rapprochés ne créent pas deux discussions).
    await session.execute(sql_text("select pg_advisory_xact_lock(hashtext(:k))"), {"k": "dm:" + ",".join(sorted(wanted))})
    candidates = (await session.scalars(
        select(ChannelMember.channel_id).join(Channel).where(Channel.kind == "dm", ChannelMember.member_id == opener))).all()
    for cid in candidates:
        ids = set((await session.scalars(select(ChannelMember.member_id).where(ChannelMember.channel_id == cid))).all())
        if ids == wanted:
            return cid, False
    ch = Channel(kind="dm", created_by=opener)
    session.add(ch)
    await session.flush()
    for mid in wanted:
        session.add(ChannelMember(channel_id=ch.id, member_id=mid, joined=True,
                                  last_read_at=now() if mid == opener else None))
    await session.commit()
    return ch.id, True


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
    if EVERYONE in mentioned:
        mentioned.discard(EVERYONE)
        mentioned |= await everyone_here(session, ch)
    valid: Set[str] = set()
    if mentioned:
        valid = set((await session.scalars(select(Member.id).where(Member.id.in_(mentioned)))).all())
        for mid in valid - {me.id}:
            session.add(Mention(message_id=msg.id, member_id=mid))
    # celui qui écrit a forcément tout lu
    await set_read(session, ch.id, me.id, msg.created_at)
    await session.commit()
    if me.kind == "agent":
        hub.touch(me.id)
    data = await emit_message(session, ch, msg, "message.new")
    from app.wake import waker
    await waker.on_message(msg, ch, me, valid)
    return data


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
