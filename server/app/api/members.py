from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import current_member
from app.api.schemas import EmailIn, MemberOut, MemberUpdate
from app.db import get_session
from app.domain.models import Member

router = APIRouter(prefix="/api/members", tags=["members"])
MANUAL_STATUSES = {None, "busy", "dnd"}
AGENT_STATUSES = {None, "working", "waiting", "blocked"}


@router.get("", response_model=List[MemberOut])
async def list_members(session: AsyncSession = Depends(get_session)):
    rows = await session.scalars(select(Member).order_by(Member.kind.desc(), Member.name))
    return rows.all()


@router.put("/{member_id}/email", response_model=MemberOut)
async def set_email(member_id: str, body: EmailIn, me: Member = Depends(current_member),
                    session: AsyncSession = Depends(get_session)):
    """L'adresse Google qui permet de se connecter. Posée par un responsable, pour la mise en ligne."""
    if me.kind != "human" or not me.is_head:
        raise HTTPException(403, "Seul un responsable règle les adresses")
    member = await session.get(Member, member_id)
    if member is None or member.kind != "human":
        raise HTTPException(404, "Membre inconnu")
    email = body.email.strip().lower()
    if email and ("@" not in email or " " in email or len(email) < 5):
        raise HTTPException(400, "Adresse invalide")
    if email:
        taken = (await session.scalars(select(Member).where(
            func.lower(Member.email) == email, Member.id != member.id))).first()
        if taken is not None:
            raise HTTPException(400, f"Déjà utilisée par {taken.name}")
    member.email = email
    await session.commit()
    from app.realtime import hub
    await hub.broadcast({"type": "member.updated", "member": MemberOut.model_validate(member).model_dump()})
    return member


@router.patch("/me", response_model=MemberOut)
async def update_me(body: MemberUpdate, me: Member = Depends(current_member),
                    session: AsyncSession = Depends(get_session)):
    data = body.model_dump(exclude_unset=True)
    allowed = AGENT_STATUSES if me.kind == "agent" else MANUAL_STATUSES
    if "manual_status" in data and data["manual_status"] not in allowed:
        raise HTTPException(400, "Statut inconnu")
    if "work_days" in data:
        days = sorted({d for d in (data["work_days"] or "").split(",") if d in {"1", "2", "3", "4", "5", "6", "7"}})
        data["work_days"] = ",".join(days)
    if "ask_hour" in data and data["ask_hour"] is not None and not 6 <= data["ask_hour"] <= 23:
        raise HTTPException(400, "Heure entre 6 h et 23 h")
    me = await session.merge(me)
    for key, value in data.items():
        setattr(me, key, value)
    await session.commit()
    from app.realtime import hub
    from app.api.schemas import MemberOut as _M
    await hub.broadcast({"type": "member.updated", "member": _M.model_validate(me).model_dump()})
    return me
