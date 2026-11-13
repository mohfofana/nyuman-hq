from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import current_member
from app.api.schemas import MemberOut, MemberUpdate
from app.db import get_session
from app.domain.models import Member

router = APIRouter(prefix="/api/members", tags=["members"])
MANUAL_STATUSES = {None, "busy", "dnd"}
AGENT_STATUSES = {None, "working", "waiting", "blocked"}


@router.get("", response_model=List[MemberOut])
async def list_members(session: AsyncSession = Depends(get_session)):
    rows = await session.scalars(select(Member).order_by(Member.kind.desc(), Member.name))
    return rows.all()


@router.patch("/me", response_model=MemberOut)
async def update_me(body: MemberUpdate, me: Member = Depends(current_member),
                    session: AsyncSession = Depends(get_session)):
    data = body.model_dump(exclude_unset=True)
    allowed = AGENT_STATUSES if me.kind == "agent" else MANUAL_STATUSES
    if "manual_status" in data and data["manual_status"] not in allowed:
        raise HTTPException(400, "Statut inconnu")
    me = await session.merge(me)
    for key, value in data.items():
        setattr(me, key, value)
    await session.commit()
    from app.realtime import hub
    from app.api.schemas import MemberOut as _M
    await hub.broadcast({"type": "member.updated", "member": _M.model_validate(me).model_dump()})
    return me
