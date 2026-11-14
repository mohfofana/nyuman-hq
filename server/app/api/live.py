"""WebSocket du temps réel et présence."""
from __future__ import annotations

import json

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import COOKIE, current_member, read_session
from app.api.chat import audience
from app.db import SessionLocal, get_session
from app.domain.models import Channel, ChannelMember, Member, PresenceLog
from app.realtime import hub

router = APIRouter(tags=["live"])


@router.get("/api/presence")
async def presence(_me: Member = Depends(current_member), session: AsyncSession = Depends(get_session)):
    ids = (await session.scalars(select(Member.id))).all()
    for row in (await session.scalars(select(PresenceLog))).all():
        hub.last_seen.setdefault(row.member_id, row.last_seen)
    return hub.all_snapshots(ids)


async def _save_last_seen(member_id: str) -> None:
    async with SessionLocal() as s:
        row = await s.get(PresenceLog, member_id)
        if row is None:
            s.add(PresenceLog(member_id=member_id, last_seen=hub.last_seen[member_id]))
        else:
            row.last_seen = hub.last_seen[member_id]
        await s.commit()


@router.websocket("/ws")
async def websocket(ws: WebSocket):
    member_id = read_session(ws.cookies.get(COOKIE))
    if not member_id:
        await ws.close(code=4401)
        return
    await ws.accept()
    await hub.connect(member_id, ws)
    try:
        while True:
            try:
                data = json.loads(await ws.receive_text())
            except ValueError:
                continue
            kind = data.get("type")
            if kind in ("active", "idle"):
                await hub.set_state(member_id, ws, kind)
            elif kind == "typing" and isinstance(data.get("channel_id"), str):
                async with SessionLocal() as s:
                    ch = await s.get(Channel, data["channel_id"])
                    if ch is None:
                        continue
                    if ch.kind == "dm" and await s.get(ChannelMember, (ch.id, member_id)) is None:
                        continue
                    to = await audience(s, ch)
                await hub.broadcast({"type": "typing", "channel_id": ch.id, "member_id": member_id,
                                     "parent_id": data.get("parent_id")}, to=to, exclude=member_id)
    except WebSocketDisconnect:
        pass
    finally:
        await hub.disconnect(member_id, ws)
        await _save_last_seen(member_id)
