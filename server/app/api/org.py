"""Organisation : départements, postes, qui tient chaque poste et quels agents l'appuient."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import current_member
from app.db import get_session
from app.domain.models import Member, Position, PositionHolder
from app.realtime import hub

router = APIRouter(prefix="/api/org", tags=["org"])
DEPARTMENTS = ["Direction générale", "Croissance", "Opérations", "Finance", "Produit et technique"]


class HoldersIn(BaseModel):
    holder_ids: List[str] = Field(default_factory=list, max_length=5)
    support_ids: List[str] = Field(default_factory=list, max_length=10)


async def snapshot(session: AsyncSession) -> dict:
    positions = (await session.scalars(select(Position).order_by(Position.id))).all()
    links = (await session.scalars(select(PositionHolder))).all()
    out = []
    for p in positions:
        out.append({
            "id": p.id, "title": p.title, "department": p.department, "reports_to": p.reports_to,
            "mission": p.mission, "hours": p.hours,
            "holder_ids": sorted(l.member_id for l in links if l.position_id == p.id and l.kind == "holder"),
            "support_ids": sorted(l.member_id for l in links if l.position_id == p.id and l.kind == "support"),
        })
    return {"departments": DEPARTMENTS, "positions": out}


@router.get("")
async def get_org(_me: Member = Depends(current_member), session: AsyncSession = Depends(get_session)):
    return await snapshot(session)


@router.put("/positions/{position_id}")
async def set_holders(position_id: int, body: HoldersIn, me: Member = Depends(current_member),
                      session: AsyncSession = Depends(get_session)):
    """Placer quelqu'un sur un poste : réservé aux heads."""
    if not me.is_head:
        raise HTTPException(403, "Seuls les heads placent les personnes sur les postes")
    if await session.get(Position, position_id) is None:
        raise HTTPException(404, "Poste introuvable")
    ids = set(body.holder_ids) | set(body.support_ids)
    members = {m.id: m for m in (await session.scalars(select(Member).where(Member.id.in_(ids)))).all()}
    if set(members) != ids:
        raise HTTPException(400, "Membres inconnus")
    if any(members[i].kind != "human" for i in body.holder_ids):
        raise HTTPException(400, "Un poste est tenu par une personne ; un agent ne peut que l'appuyer")
    if any(members[i].kind != "agent" for i in body.support_ids):
        raise HTTPException(400, "L'appui est réservé aux agents")
    await session.execute(delete(PositionHolder).where(PositionHolder.position_id == position_id))
    for mid in body.holder_ids:
        session.add(PositionHolder(position_id=position_id, member_id=mid, kind="holder"))
    for mid in body.support_ids:
        session.add(PositionHolder(position_id=position_id, member_id=mid, kind="support"))
    await session.commit()
    data = await snapshot(session)
    await hub.broadcast({"type": "org.updated"})
    return data
