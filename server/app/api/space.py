"""« Mon espace » : chacun arrive sur un poste de travail préparé pour son métier.

Le contenu suit le POSTE tenu dans l'organigramme (pas la personne) :
1 DG · 2 Coordination · 3-6 Croissance · 7-8 Opérations et juridique · 9 Finance · 10-12 Produit et technique.
Ici aussi : les suivis (salons, échéances, dépenses) et la salle du conseil (propositions + vote des heads).
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import current_member
from app.api.timesheet import TZ, today_local
from app.db import get_session
from app.domain.models import (AgentRun, Channel, Member, Message, Position, PositionHolder, Project, Proposal, Task,
                               TimeEntry, TrackItem, Vote)
from app.realtime import hub, now

router = APIRouter(prefix="/api", tags=["space"])

ROLE_OF_POSITION = {1: "dg", 2: "coord", 3: "growth", 4: "growth", 5: "growth", 6: "growth",
                    7: "ops", 8: "ops", 9: "finance", 10: "tech", 11: "tech", 12: "tech"}
DEPARTMENT_OF_ROLE = {"growth": "Croissance", "ops": "Opérations", "finance": "Finance", "tech": "Produit et technique"}
# Le poste de responsable de chaque département : sert à savoir à qui s'adresser.
HEAD_POSITION_OF_ROLE = {"growth": 3, "ops": 7, "finance": 9, "tech": 10}
LAUNCH_DAY = date(2026, 12, 12)

# Étapes de chaque liste de suivi (la première est l'étape de départ).
STAGES = {
    "salon": ["à contacter", "contacté", "inscrit", "1re réservation"],
    "echeance": ["à faire", "en cours", "réglé"],
    "depense": ["à valider", "validée", "refusée"],
}
CHOICES = ("pour", "contre", "abstention")
CRITIC = "koffi"


# ---------- schémas ----------
class TrackIn(BaseModel):
    kind: str
    title: str = Field(min_length=1, max_length=200)
    stage: Optional[str] = None
    owner_id: Optional[str] = None
    due_date: Optional[date] = None
    amount: Optional[int] = Field(default=None, ge=0, le=10**12)
    currency: str = Field(default="FCFA", max_length=6)
    contact: str = Field(default="", max_length=160)
    note: str = Field(default="", max_length=4000)


class TrackPatch(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    stage: Optional[str] = None
    owner_id: Optional[str] = None
    due_date: Optional[date] = None
    amount: Optional[int] = Field(default=None, ge=0, le=10**12)
    currency: Optional[str] = Field(default=None, max_length=6)
    contact: Optional[str] = Field(default=None, max_length=160)
    note: Optional[str] = Field(default=None, max_length=4000)
    archived: Optional[bool] = None


class ProposalIn(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    body: str = Field(default="", max_length=10000)
    figures: str = Field(default="", max_length=4000)
    deadline: Optional[date] = None
    ask_critic: bool = True


class VoteIn(BaseModel):
    choice: str
    comment: str = Field(default="", max_length=500)


class OpinionIn(BaseModel):
    opinion: str = Field(min_length=1, max_length=6000)


# ---------- outils ----------
def track_out(t: TrackItem) -> dict:
    return {"id": t.id, "kind": t.kind, "title": t.title, "stage": t.stage, "owner_id": t.owner_id, "due_date": t.due_date,
            "amount": t.amount, "currency": t.currency, "contact": t.contact, "note": t.note, "archived": t.archived,
            "created_by": t.created_by, "decided_by": t.decided_by, "created_at": t.created_at, "updated_at": t.updated_at}


async def heads(session: AsyncSession) -> List[Member]:
    return list((await session.scalars(select(Member).where(Member.kind == "human", Member.is_head.is_(True))
                                       .order_by(Member.name))).all())


async def proposal_out(session: AsyncSession, p: Proposal) -> dict:
    votes = (await session.scalars(select(Vote).where(Vote.proposal_id == p.id).order_by(Vote.created_at))).all()
    voters = [h.id for h in await heads(session)]
    tally = {c: sum(1 for v in votes if v.choice == c) for c in CHOICES}
    return {"id": p.id, "title": p.title, "body": p.body, "figures": p.figures, "author_id": p.author_id, "status": p.status,
            "deadline": p.deadline, "opinion": p.opinion, "opinion_by": p.opinion_by, "created_at": p.created_at,
            "closed_at": p.closed_at, "voters": voters, "tally": tally,
            "votes": [{"member_id": v.member_id, "choice": v.choice, "comment": v.comment, "created_at": v.created_at} for v in votes]}


def is_head(m: Member) -> bool:
    return m.kind == "human" and m.is_head


async def broadcast_proposal(session: AsyncSession, p: Proposal) -> dict:
    data = await proposal_out(session, p)
    await hub.broadcast({"type": "proposal.updated", "proposal": data})
    return data


# ---------- suivis ----------
@router.get("/tracks")
async def list_tracks(kind: str, archived: bool = False, _me: Member = Depends(current_member),
                      session: AsyncSession = Depends(get_session)):
    if kind not in STAGES:
        raise HTTPException(400, "Liste inconnue")
    rows = (await session.scalars(select(TrackItem).where(TrackItem.kind == kind, TrackItem.archived.is_(archived))
                                  .order_by(TrackItem.due_date.asc().nulls_last(), TrackItem.created_at.desc()))).all()
    return [track_out(t) for t in rows]


async def check_owner(session: AsyncSession, owner_id: Optional[str]) -> None:
    if owner_id and await session.get(Member, owner_id) is None:
        raise HTTPException(400, "Membre inconnu")


@router.post("/tracks", status_code=201)
async def add_track(body: TrackIn, me: Member = Depends(current_member), session: AsyncSession = Depends(get_session)):
    if body.kind not in STAGES:
        raise HTTPException(400, "Liste inconnue")
    stage = body.stage or STAGES[body.kind][0]
    if stage not in STAGES[body.kind]:
        raise HTTPException(400, "Étape inconnue")
    if body.kind == "depense" and stage != "à valider":
        raise HTTPException(400, "Une dépense commence toujours « à valider »")
    await check_owner(session, body.owner_id)
    t = TrackItem(kind=body.kind, title=body.title.strip(), stage=stage, owner_id=body.owner_id or me.id,
                  due_date=body.due_date, amount=body.amount, currency=body.currency or "FCFA",
                  contact=body.contact.strip(), note=body.note.strip(), created_by=me.id, updated_at=now())
    session.add(t)
    await session.commit()
    await hub.broadcast({"type": "track.updated", "kind": t.kind})
    return track_out(t)


@router.patch("/tracks/{tid}")
async def edit_track(tid: str, body: TrackPatch, me: Member = Depends(current_member), session: AsyncSession = Depends(get_session)):
    t = await session.get(TrackItem, tid)
    if t is None:
        raise HTTPException(404, "Ligne introuvable")
    data = body.model_dump(exclude_unset=True)
    if "stage" in data:
        if data["stage"] not in STAGES[t.kind]:
            raise HTTPException(400, "Étape inconnue")
        # Valider ou refuser une dépense : un head seulement, jamais un agent.
        if t.kind == "depense" and data["stage"] != t.stage:
            if not is_head(me):
                raise HTTPException(403, "Seul un responsable valide ou refuse une dépense")
            t.decided_by = me.id if data["stage"] != "à valider" else None
    await check_owner(session, data.get("owner_id"))
    for k, v in data.items():
        setattr(t, k, v.strip() if isinstance(v, str) else v)
    t.updated_at = now()
    await session.commit()
    await hub.broadcast({"type": "track.updated", "kind": t.kind})
    return track_out(t)


# ---------- salle du conseil ----------
@router.get("/proposals")
async def list_proposals(status: Optional[str] = None, _me: Member = Depends(current_member),
                         session: AsyncSession = Depends(get_session)):
    q = select(Proposal)
    if status == "open":
        q = q.where(Proposal.status == "open")
    elif status == "closed":
        q = q.where(Proposal.status != "open")
    rows = (await session.scalars(q.order_by(Proposal.created_at.desc()).limit(100))).all()
    return [await proposal_out(session, p) for p in rows]


@router.get("/proposals/{pid}")
async def get_proposal(pid: str, _me: Member = Depends(current_member), session: AsyncSession = Depends(get_session)):
    p = await session.get(Proposal, pid)
    if p is None:
        raise HTTPException(404, "Proposition introuvable")
    return await proposal_out(session, p)


@router.post("/proposals", status_code=201)
async def add_proposal(body: ProposalIn, me: Member = Depends(current_member), session: AsyncSession = Depends(get_session)):
    """Tout membre peut proposer (les agents aussi : ils préparent, les heads tranchent)."""
    p = Proposal(title=body.title.strip(), body=body.body.strip(), figures=body.figures.strip(), author_id=me.id,
                 deadline=body.deadline, created_at=now())
    session.add(p)
    await session.commit()
    data = await broadcast_proposal(session, p)
    await announce(p, me, body.ask_critic)
    return data


async def announce(p: Proposal, author: Member, ask_critic: bool) -> None:
    """Annonce dans #général avec la carte de vote ; Koffi est mentionné pour donner son avis (ce qui le réveille)."""
    from app.api.chat import emit_message
    from app.db import SessionLocal

    async with SessionLocal() as s:
        ch = await s.get(Channel, "general")
        if ch is None:
            return
        critic = ask_critic and author.id != CRITIC and await s.get(Member, CRITIC) is not None
        text = f"<proposal:{p.id}>" + (f"\n<@{CRITIC}> votre avis, avec des chiffres et une alternative ? (outil hq_avis_proposition)" if critic else "")
        msg = Message(channel_id=ch.id, author_id=author.id, body=text, created_at=now())
        s.add(msg)
        await s.flush()
        if critic:
            from app.domain.models import Mention
            s.add(Mention(message_id=msg.id, member_id=CRITIC))
        await s.commit()
        await emit_message(s, ch, msg, "message.new")
        if critic:
            from app.wake import waker
            await waker.on_message(msg, ch, author, {CRITIC}, force=True)


@router.post("/proposals/{pid}/vote")
async def vote(pid: str, body: VoteIn, me: Member = Depends(current_member), session: AsyncSession = Depends(get_session)):
    if not is_head(me):
        raise HTTPException(403, "Seuls les responsables votent")
    if body.choice not in CHOICES:
        raise HTTPException(400, "Choix inconnu")
    p = await session.get(Proposal, pid)
    if p is None or p.status != "open":
        raise HTTPException(400, "Le vote est clos")
    v = await session.get(Vote, (pid, me.id))
    if v is None:
        session.add(Vote(proposal_id=pid, member_id=me.id, choice=body.choice, comment=body.comment.strip(), created_at=now()))
    else:
        v.choice, v.comment, v.created_at = body.choice, body.comment.strip(), now()
    await session.flush()
    # Quand tous les responsables ont voté, le résultat tombe tout seul.
    voted = await session.scalar(select(func.count()).select_from(Vote).where(Vote.proposal_id == pid))
    if voted >= len(await heads(session)):
        await close(session, p)
    await session.commit()
    return await broadcast_proposal(session, p)


async def close(session: AsyncSession, p: Proposal) -> None:
    votes = (await session.scalars(select(Vote).where(Vote.proposal_id == p.id))).all()
    yes = sum(1 for v in votes if v.choice == "pour")
    no = sum(1 for v in votes if v.choice == "contre")
    p.status = "adopted" if yes > no else "rejected"
    p.closed_at = now()


@router.post("/proposals/{pid}/close")
async def close_vote(pid: str, me: Member = Depends(current_member), session: AsyncSession = Depends(get_session)):
    """Clore avant que tout le monde ait voté (un responsable) : majorité des votes exprimés, égalité = rejetée."""
    if not is_head(me):
        raise HTTPException(403, "Seul un responsable clôt un vote")
    p = await session.get(Proposal, pid)
    if p is None or p.status != "open":
        raise HTTPException(400, "Déjà clos")
    await close(session, p)
    await session.commit()
    return await broadcast_proposal(session, p)


@router.post("/proposals/{pid}/withdraw")
async def withdraw(pid: str, me: Member = Depends(current_member), session: AsyncSession = Depends(get_session)):
    p = await session.get(Proposal, pid)
    if p is None or p.status != "open":
        raise HTTPException(400, "Déjà clos")
    if p.author_id != me.id:
        raise HTTPException(403, "Seul l'auteur retire sa proposition")
    p.status, p.closed_at = "withdrawn", now()
    await session.commit()
    return await broadcast_proposal(session, p)


@router.put("/proposals/{pid}/opinion")
async def set_opinion(pid: str, body: OpinionIn, me: Member = Depends(current_member), session: AsyncSession = Depends(get_session)):
    """L'avis du contradicteur (Koffi), affiché au-dessus du vote."""
    if me.id != CRITIC:
        raise HTTPException(403, "L'avis est donné par Koffi")
    p = await session.get(Proposal, pid)
    if p is None:
        raise HTTPException(404, "Proposition introuvable")
    p.opinion, p.opinion_by = body.opinion.strip(), me.id
    await session.commit()
    return await broadcast_proposal(session, p)


# ---------- mon espace ----------
async def my_roles(session: AsyncSession, me: Member):
    links = (await session.execute(select(PositionHolder.position_id, PositionHolder.kind).where(
        PositionHolder.member_id == me.id))).all()
    held = [pid for pid, kind in links if kind == "holder"]
    positions = (await session.scalars(select(Position).where(Position.id.in_(held)).order_by(Position.id))).all() if held else []
    roles = []
    for p in positions:
        r = ROLE_OF_POSITION.get(p.id)
        if r and r not in roles:
            roles.append(r)
    # l'agent qui appuie chacun de mes postes
    support = (await session.scalars(select(PositionHolder.member_id).where(
        PositionHolder.position_id.in_(held), PositionHolder.kind == "support"))).all() if held else []
    return roles, positions, list(dict.fromkeys(support))


def mini_task(t: Task, projects: Dict[str, Project]) -> dict:
    p = projects.get(t.project_id)
    return {"id": t.id, "title": t.title, "status": t.status, "priority": t.priority, "assignee_id": t.assignee_id,
            "due_date": t.due_date, "project_id": t.project_id, "project_name": p.name if p else "", "project_icon": p.icon if p else "📁"}


@router.get("/space")
async def my_space(me: Member = Depends(current_member), session: AsyncSession = Depends(get_session)):
    roles, positions, agents = await my_roles(session, me)
    today = today_local()
    projects = {p.id: p for p in (await session.scalars(select(Project).where(Project.archived.is_(False)))).all()}
    open_tasks = list((await session.scalars(select(Task).where(
        Task.archived.is_(False), Task.status != "done", Task.project_id.in_(list(projects) or [""])))).all())
    week_ago = now() - timedelta(days=7)
    done_week = list((await session.scalars(select(Task).where(
        Task.archived.is_(False), Task.status == "done", Task.completed_at >= week_ago))).all())
    out: dict = {"roles": roles, "agents": agents,
                 "positions": [{"id": p.id, "title": p.title, "department": p.department} for p in positions],
                 "is_head": is_head(me), "today": today}

    # À voter : pour chaque responsable
    if is_head(me):
        open_props = (await session.scalars(select(Proposal).where(Proposal.status == "open").order_by(Proposal.created_at))).all()
        mine = set((await session.scalars(select(Vote.proposal_id).where(Vote.member_id == me.id))).all())
        out["to_vote"] = [{"id": p.id, "title": p.title, "author_id": p.author_id, "deadline": p.deadline,
                           "has_opinion": bool(p.opinion)} for p in open_props if p.id not in mine]

    def dept_tasks(dept: str):
        return [t for t in open_tasks if projects.get(t.project_id) and projects[t.project_id].department == dept]

    def overdue(ts):
        return [t for t in ts if t.due_date and t.due_date < today]

    if "dg" in roles or "coord" in roles:
        heads_by_position = {}
        for pid, mid in (await session.execute(select(PositionHolder.position_id, PositionHolder.member_id).where(
                PositionHolder.position_id.in_(list(HEAD_POSITION_OF_ROLE.values())), PositionHolder.kind == "holder"))).all():
            heads_by_position.setdefault(pid, mid)
        depts = []
        for role, dept in DEPARTMENT_OF_ROLE.items():
            ts = dept_tasks(dept)
            done = [t for t in done_week if projects.get(t.project_id) and projects[t.project_id].department == dept]
            late = overdue(ts)
            depts.append({"role": role, "department": dept, "open": len(ts), "overdue": len(late),
                          "done_week": len(done), "review": sum(1 for t in ts if t.status == "review"),
                          "head_id": heads_by_position.get(HEAD_POSITION_OF_ROLE[role]),
                          "late_titles": [t.title for t in late[:3]]})
        out["departments"] = depts
        # budgets d'heures à surveiller (80 % et plus)
        used = dict((await session.execute(select(TimeEntry.project_id, func.sum(TimeEntry.minutes)).group_by(TimeEntry.project_id))).all())
        out["budget_alerts"] = [{"id": p.id, "name": p.name, "icon": p.icon, "hours_budget": p.hours_budget,
                                 "used_minutes": int(used.get(p.id) or 0), "pct": round(int(used.get(p.id) or 0) / (p.hours_budget * 60) * 100)}
                                for p in projects.values() if p.hours_budget and int(used.get(p.id) or 0) >= p.hours_budget * 60 * 0.8]
    if "coord" in roles:
        soon = today + timedelta(days=7)
        out["week_due"] = [mini_task(t, projects) for t in sorted(
            [t for t in open_tasks if t.due_date and t.due_date <= soon], key=lambda t: t.due_date)][:30]
        last_move = dict((await session.execute(select(Task.project_id, func.max(Task.updated_at)).group_by(Task.project_id))).all())
        cut = now() - timedelta(days=14)
        out["quiet_projects"] = [{"id": p.id, "name": p.name, "icon": p.icon, "owner_id": p.owner_id}
                                 for p in projects.values() if p.created_at < cut and (last_move.get(p.id) is None or last_move[p.id] < cut)]
    if "dg" in roles or "finance" in roles:
        pend = (await session.scalars(select(TrackItem).where(TrackItem.kind == "depense", TrackItem.archived.is_(False),
                                                              TrackItem.stage == "à valider"))).all()
        out["spend_pending"] = {"count": len(pend), "items": [track_out(t) for t in pend[:5]]}
    if "finance" in roles or "dg" in roles:
        month_start = datetime(today.year, today.month, 1, tzinfo=TZ)
        cost = await session.scalar(select(func.coalesce(func.sum(AgentRun.cost_usd), 0)).where(AgentRun.created_at >= month_start))
        runs = await session.scalar(select(func.count()).select_from(AgentRun).where(AgentRun.created_at >= month_start,
                                                                                     AgentRun.status == "done"))
        out["ai_cost"] = {"month_usd": round(float(cost or 0), 2), "replies": int(runs or 0)}
    if "growth" in roles:
        rows = dict((await session.execute(select(TrackItem.stage, func.count()).where(
            TrackItem.kind == "salon", TrackItem.archived.is_(False)).group_by(TrackItem.stage))).all())
        out["salons"] = {s: int(rows.get(s, 0)) for s in STAGES["salon"]}
        out["launch_days"] = (LAUNCH_DAY - today).days
    if "ops" in roles:
        horizon = today + timedelta(days=30)
        items = (await session.scalars(select(TrackItem).where(
            TrackItem.kind == "echeance", TrackItem.archived.is_(False), TrackItem.stage != "réglé")
            .order_by(TrackItem.due_date.asc().nulls_last()))).all()
        out["deadlines"] = [track_out(t) for t in items if t.due_date is None or t.due_date <= horizon][:8]
    for role in ("growth", "ops", "finance", "tech"):
        if role in roles:
            ts = dept_tasks(DEPARTMENT_OF_ROLE[role])
            out.setdefault("dept", {})[role] = {
                "department": DEPARTMENT_OF_ROLE[role], "open": len(ts), "overdue": len(overdue(ts)),
                "urgent": [mini_task(t, projects) for t in sorted(ts, key=lambda t: (t.priority != "high", t.due_date or date.max))
                           if t.priority == "high" or (t.due_date and t.due_date <= today + timedelta(days=3))][:6],
            }
    return out
