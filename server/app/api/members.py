from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import current_member
from app.api.schemas import EmailIn, MemberOut, MemberUpdate
from app.db import get_session
from app.domain.models import JoinRequest, Member, MemberEmail

router = APIRouter(prefix="/api/members", tags=["members"])
MANUAL_STATUSES = {None, "busy", "dnd"}
AGENT_STATUSES = {None, "working", "waiting", "blocked"}


async def with_emails(session: AsyncSession, members: List[Member]) -> List[dict]:
    """Chaque fiche porte ses adresses de connexion (une pro, une perso…)."""
    by_member: dict[str, list[str]] = {}
    for email, mid in (await session.execute(select(MemberEmail.email, MemberEmail.member_id))).all():
        by_member.setdefault(mid, []).append(email)
    out = []
    for m in members:
        d = MemberOut.model_validate(m).model_dump()
        d["emails"] = sorted(by_member.get(m.id, []))
        out.append(d)
    return out


@router.get("", response_model=List[MemberOut])
async def list_members(_me: Member = Depends(current_member), session: AsyncSession = Depends(get_session)):
    """Réservé aux membres : la liste porte les noms, les postes et les adresses de l'équipe."""
    rows = list((await session.scalars(select(Member).order_by(Member.kind.desc(), Member.name))).all())
    return await with_emails(session, rows)


# ---------- demandes à confirmer (quelqu'un s'est présenté lui-même) ----------
@router.get("/join-requests")
async def join_requests(me: Member = Depends(current_member), session: AsyncSession = Depends(get_session)):
    """Les personnes qui se sont présentées et attendent qu'un responsable confirme."""
    if me.kind != "human" or not me.is_head:
        return []
    rows = (await session.scalars(select(JoinRequest).order_by(JoinRequest.created_at))).all()
    names = {m.id: m.name for m in (await session.scalars(select(Member))).all()}
    return [{"email": r.email, "member_id": r.member_id, "member_name": names.get(r.member_id, r.member_id),
             "name_seen": r.name_seen, "created_at": r.created_at} for r in rows]


@router.post("/join-requests/{email}/{decision}", response_model=MemberOut)
async def decide_join(email: str, decision: str, me: Member = Depends(current_member),
                      session: AsyncSession = Depends(get_session)):
    """Oui : l'adresse est rangée sur la fiche et la personne entre. Non : la demande disparaît."""
    if me.kind != "human" or not me.is_head:
        raise HTTPException(403, "Seul un responsable confirme")
    if decision not in ("oui", "non"):
        raise HTTPException(400, "Décision inconnue")
    req = await session.get(JoinRequest, email.strip().lower())
    if req is None:
        raise HTTPException(404, "Demande introuvable")
    member = await session.get(Member, req.member_id)
    if decision == "oui" and await session.get(MemberEmail, req.email) is None:
        session.add(MemberEmail(email=req.email, member_id=req.member_id, added_by=me.id))
    await session.delete(req)
    await session.commit()
    from app.realtime import hub
    await hub.broadcast({"type": "join.decided", "email": email, "ok": decision == "oui"})
    return await broadcast_member(session, member)


@router.post("/{member_id}/emails", response_model=MemberOut)
async def add_email(member_id: str, body: EmailIn, me: Member = Depends(current_member),
                    session: AsyncSession = Depends(get_session)):
    """Ajoute une adresse Google à quelqu'un : la pro, la perso, autant qu'il en faut."""
    member = await head_target(session, me, member_id)
    email = body.email.strip().lower()
    if "@" not in email or " " in email or len(email) < 5 or "." not in email.split("@")[-1]:
        raise HTTPException(400, "Adresse invalide")
    taken = await session.get(MemberEmail, email)
    if taken is not None:
        if taken.member_id == member.id:
            return (await with_emails(session, [member]))[0]
        other = await session.get(Member, taken.member_id)
        raise HTTPException(400, f"Déjà utilisée par {other.name if other else 'quelqu un d autre'}")
    session.add(MemberEmail(email=email, member_id=member.id, added_by=me.id))
    await session.commit()
    return await broadcast_member(session, member)


@router.delete("/{member_id}/emails/{email}", response_model=MemberOut)
async def remove_email(member_id: str, email: str, me: Member = Depends(current_member),
                       session: AsyncSession = Depends(get_session)):
    member = await head_target(session, me, member_id)
    row = await session.get(MemberEmail, email.strip().lower())
    if row is not None and row.member_id == member.id:
        await session.delete(row)
        await session.commit()
    return await broadcast_member(session, member)


async def head_target(session: AsyncSession, me: Member, member_id: str) -> Member:
    if me.kind != "human" or not me.is_head:
        raise HTTPException(403, "Seul un responsable règle les adresses")
    member = await session.get(Member, member_id)
    if member is None or member.kind != "human":
        raise HTTPException(404, "Membre inconnu")
    return member


async def broadcast_member(session: AsyncSession, member: Member) -> dict:
    data = (await with_emails(session, [member]))[0]
    from app.realtime import hub
    await hub.broadcast({"type": "member.updated", "member": data})
    return data


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
