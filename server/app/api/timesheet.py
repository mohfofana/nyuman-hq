"""Suivi du temps façon Gryzzly : chacun déclare lui-même où est passé son temps (rien n'est mesuré en cachette).

- Mariam pose la question le soir des jours travaillés, en message privé (une carte à remplir en 10 secondes).
- Chacun voit son propre temps ; les heads voient le temps par projet et par personne, et les budgets d'heures.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Dict, List, Optional
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import current_member
from app.db import SessionLocal, get_session
from app.domain.models import Channel, Member, Message, Project, Task, TimeAsk, TimeEntry
from app.realtime import hub, now

router = APIRouter(prefix="/api/time", tags=["time"])
TZ = ZoneInfo("Africa/Abidjan")
ASKER = "mariam"
LAST_ASK_HOUR = 23  # passé 23 h, on ne demande plus rien ce jour-là
CARD = "<temps:{}>"


def today_local(at: Optional[datetime] = None) -> date:
    return (at or now()).astimezone(TZ).date()


# ---------- schémas ----------
class EntryIn(BaseModel):
    day: date
    project_id: Optional[str] = None
    task_id: Optional[str] = None
    minutes: int = Field(ge=5, le=16 * 60)
    note: str = Field(default="", max_length=300)


class EntryPatch(BaseModel):
    minutes: Optional[int] = Field(default=None, ge=5, le=16 * 60)
    note: Optional[str] = Field(default=None, max_length=300)


class DayOff(BaseModel):
    day: date


def entry_out(e: TimeEntry, projects: Dict[str, Project], tasks: Dict[str, Task]) -> dict:
    p, t = projects.get(e.project_id), tasks.get(e.task_id or "")
    return {"id": e.id, "member_id": e.member_id, "day": e.day, "project_id": e.project_id,
            "project_name": p.name if p else "", "project_icon": p.icon if p else "📁",
            "task_id": e.task_id, "task_title": t.title if t else None, "minutes": e.minutes, "note": e.note}


async def lookup(session: AsyncSession, entries: List[TimeEntry]):
    pids = {e.project_id for e in entries}
    tids = {e.task_id for e in entries if e.task_id}
    projects = {p.id: p for p in (await session.scalars(select(Project).where(Project.id.in_(pids)))).all()} if pids else {}
    tasks = {t.id: t for t in (await session.scalars(select(Task).where(Task.id.in_(tids)))).all()} if tids else {}
    return projects, tasks


def check_day(day: date) -> None:
    today = today_local()
    if day > today or day < today - timedelta(days=60):
        raise HTTPException(400, "Jour hors de la période (60 derniers jours)")


def humans_only(me: Member) -> None:
    if me.kind != "human":
        raise HTTPException(403, "Le suivi du temps concerne les humains")


async def set_ask(session: AsyncSession, member_id: str, day: date, state: str) -> None:
    stmt = pg_insert(TimeAsk).values(member_id=member_id, day=day, state=state)
    await session.execute(stmt.on_conflict_do_update(index_elements=["member_id", "day"], set_={"state": state}))


# ---------- ma saisie ----------
@router.get("/me")
async def my_time(start: Optional[date] = None, end: Optional[date] = None,
                  me: Member = Depends(current_member), session: AsyncSession = Depends(get_session)):
    end = end or today_local()
    start = start or end - timedelta(days=6)
    rows = list((await session.scalars(select(TimeEntry).where(
        TimeEntry.member_id == me.id, TimeEntry.day >= start, TimeEntry.day <= end).order_by(TimeEntry.day, TimeEntry.created_at))).all())
    projects, tasks = await lookup(session, rows)
    asks = (await session.scalars(select(TimeAsk).where(
        TimeAsk.member_id == me.id, TimeAsk.day >= start, TimeAsk.day <= end))).all()
    return {"start": start, "end": end, "entries": [entry_out(e, projects, tasks) for e in rows],
            "days_off": [a.day for a in asks if a.state == "off"],
            "work_days": me.work_days, "ask_hour": me.ask_hour}


@router.get("/suggestions")
async def suggestions(day: Optional[date] = None, me: Member = Depends(current_member), session: AsyncSession = Depends(get_session)):
    """Ce qui a le plus de chances d'être juste : mes tâches en cours ou finies ce jour-là, puis mes projets récents."""
    day = day or today_local()
    mine = (await session.scalars(select(Task).where(
        Task.assignee_id == me.id, Task.archived.is_(False), Task.status.in_(("doing", "review", "done")))
        .order_by(Task.updated_at.desc()).limit(40))).all()
    picked = [t for t in mine if t.status != "done" or (t.completed_at and t.completed_at.astimezone(TZ).date() >= day - timedelta(days=1))][:8]
    recent = (await session.execute(select(TimeEntry.project_id, func.max(TimeEntry.day)).where(
        TimeEntry.member_id == me.id, TimeEntry.day >= day - timedelta(days=30)).group_by(TimeEntry.project_id)
        .order_by(func.max(TimeEntry.day).desc()))).all()
    projects = (await session.scalars(select(Project).where(Project.archived.is_(False)).order_by(Project.name))).all()
    by_id = {p.id: p for p in projects}
    order = [pid for pid, _ in recent if pid in by_id] + [t.project_id for t in picked if t.project_id in by_id] + \
            [p.id for p in projects if p.owner_id == me.id] + [p.id for p in projects]
    seen, ranked = set(), []
    for pid in order:
        if pid not in seen:
            seen.add(pid)
            ranked.append(pid)
    return {"day": day,
            "tasks": [{"id": t.id, "title": t.title, "status": t.status, "project_id": t.project_id,
                       "project_name": by_id[t.project_id].name if t.project_id in by_id else ""} for t in picked],
            "projects": [{"id": pid, "name": by_id[pid].name, "icon": by_id[pid].icon} for pid in ranked]}


@router.post("", status_code=201)
async def add_entry(body: EntryIn, me: Member = Depends(current_member), session: AsyncSession = Depends(get_session)):
    humans_only(me)
    check_day(body.day)
    project_id = body.project_id
    if body.task_id:
        t = await session.get(Task, body.task_id)
        if t is None:
            raise HTTPException(400, "Tâche introuvable")
        project_id = t.project_id
    if not project_id or await session.get(Project, project_id) is None:
        raise HTTPException(400, "Choisissez un projet ou une tâche")
    before = await project_minutes(session, project_id)
    e = TimeEntry(member_id=me.id, day=body.day, project_id=project_id, task_id=body.task_id,
                  minutes=body.minutes, note=body.note.strip())
    session.add(e)
    await set_ask(session, me.id, body.day, "answered")
    await session.commit()
    await budget_alert(project_id, before, before + body.minutes)
    await hub.broadcast({"type": "time.updated", "member_id": me.id, "day": str(body.day)}, to={me.id})
    projects, tasks = await lookup(session, [e])
    return entry_out(e, projects, tasks)


async def own_entry(session: AsyncSession, eid: str, me: Member) -> TimeEntry:
    e = await session.get(TimeEntry, eid)
    if e is None or e.member_id != me.id:
        raise HTTPException(404, "Saisie introuvable")
    return e


@router.patch("/{eid}")
async def edit_entry(eid: str, body: EntryPatch, me: Member = Depends(current_member), session: AsyncSession = Depends(get_session)):
    e = await own_entry(session, eid, me)
    for k, v in body.model_dump(exclude_unset=True).items():
        if v is not None:
            setattr(e, k, v.strip() if isinstance(v, str) else v)
    await session.commit()
    await hub.broadcast({"type": "time.updated", "member_id": me.id, "day": str(e.day)}, to={me.id})
    projects, tasks = await lookup(session, [e])
    return entry_out(e, projects, tasks)


@router.delete("/{eid}", status_code=204)
async def delete_entry(eid: str, me: Member = Depends(current_member), session: AsyncSession = Depends(get_session)):
    e = await own_entry(session, eid, me)
    day = e.day
    await session.delete(e)
    await session.commit()
    await hub.broadcast({"type": "time.updated", "member_id": me.id, "day": str(day)}, to={me.id})


@router.post("/off", status_code=204)
async def day_off(body: DayOff, me: Member = Depends(current_member), session: AsyncSession = Depends(get_session)):
    """« Pas travaillé ce jour-là » : la question est close, sans rien à justifier."""
    humans_only(me)
    check_day(body.day)
    await set_ask(session, me.id, body.day, "off")
    await session.commit()
    await hub.broadcast({"type": "time.updated", "member_id": me.id, "day": str(body.day)}, to={me.id})


@router.delete("/off/{day}", status_code=204)
async def undo_day_off(day: date, me: Member = Depends(current_member), session: AsyncSession = Depends(get_session)):
    a = await session.get(TimeAsk, (me.id, day))
    if a is not None and a.state == "off":
        a.state = "asked"
        await session.commit()
    await hub.broadcast({"type": "time.updated", "member_id": me.id, "day": str(day)}, to={me.id})


# ---------- vue d'équipe ----------
async def project_minutes(session: AsyncSession, project_id: str) -> int:
    return int((await session.scalar(select(func.coalesce(func.sum(TimeEntry.minutes), 0)).where(
        TimeEntry.project_id == project_id))) or 0)


@router.get("/team")
async def team(days: int = 7, me: Member = Depends(current_member), session: AsyncSession = Depends(get_session)):
    """Temps par projet (tout le monde) ; par personne seulement pour les heads. Jamais d'heures de connexion."""
    days = max(1, min(days, 92))
    end = today_local()
    start = end - timedelta(days=days - 1)
    projects = (await session.scalars(select(Project).where(Project.archived.is_(False)).order_by(Project.name))).all()
    period = dict((await session.execute(select(TimeEntry.project_id, func.sum(TimeEntry.minutes)).where(
        TimeEntry.day >= start, TimeEntry.day <= end).group_by(TimeEntry.project_id))).all())
    total = dict((await session.execute(select(TimeEntry.project_id, func.sum(TimeEntry.minutes))
                                        .group_by(TimeEntry.project_id))).all())
    last = dict((await session.execute(select(TimeEntry.project_id, func.max(TimeEntry.day))
                                       .group_by(TimeEntry.project_id))).all())
    out_projects = []
    for p in projects:
        used = int(total.get(p.id) or 0)
        out_projects.append({
            "id": p.id, "name": p.name, "icon": p.icon, "owner_id": p.owner_id,
            "minutes": int(period.get(p.id) or 0), "total_minutes": used, "hours_budget": p.hours_budget,
            "budget_pct": round(used / (p.hours_budget * 60) * 100) if p.hours_budget else None,
            "last_day": last.get(p.id),
            # « inactif » façon Gryzzly : du temps a déjà été passé dessus, mais plus rien depuis 14 jours
            "inactive": bool(last.get(p.id) and last[p.id] < end - timedelta(days=14)),
        })
    people = None
    if me.is_head and me.kind == "human":
        rows = (await session.execute(select(TimeEntry.member_id, TimeEntry.project_id, func.sum(TimeEntry.minutes)).where(
            TimeEntry.day >= start, TimeEntry.day <= end).group_by(TimeEntry.member_id, TimeEntry.project_id))).all()
        people = {}
        for mid, pid, mins in rows:
            d = people.setdefault(mid, {"member_id": mid, "minutes": 0, "projects": {}})
            d["minutes"] += int(mins)
            d["projects"][pid] = int(mins)
        people = sorted(people.values(), key=lambda d: -d["minutes"])
    return {"start": start, "end": end, "days": days, "projects": out_projects, "people": people}


# ---------- alertes et question du soir (postées par Mariam, sans IA : aucun coût) ----------
async def post_as_asker(session: AsyncSession, member_id: str, body: str) -> Optional[Message]:
    from app.api.chat import emit_message, ensure_dm

    if await session.get(Member, ASKER) is None or member_id == ASKER:
        return None
    cid, created = await ensure_dm(session, {ASKER, member_id}, ASKER)
    msg = Message(channel_id=cid, author_id=ASKER, body=body, created_at=now())
    session.add(msg)
    await session.commit()
    if created:
        await hub.broadcast({"type": "channel.created", "channel_id": cid}, to={ASKER, member_id})
    await emit_message(session, await session.get(Channel, cid), msg, "message.new")
    return msg


def fmt_hours(minutes: int) -> str:
    h, m = divmod(int(minutes), 60)
    return f"{h} h {m:02d}" if m else f"{h} h"


async def budget_alert(project_id: str, before: int, after: int) -> None:
    """Prévient le responsable du projet quand on franchit 80 % puis 100 % du budget d'heures."""
    async with SessionLocal() as s:
        p = await s.get(Project, project_id)
        if p is None or not p.hours_budget or not p.owner_id:
            return
        budget = p.hours_budget * 60
        for pct in (100, 80):
            if before < budget * pct / 100 <= after:
                word = "a dépassé son budget d'heures" if pct == 100 else "a utilisé 80 % de son budget d'heures"
                await post_as_asker(s, p.owner_id, f"⏱️ Le projet **{p.name}** {word} : {fmt_hours(after)} sur {p.hours_budget} h.")
                return


async def send_time_asks(at: Optional[datetime] = None) -> List[str]:
    """Le soir des jours travaillés de chacun, Mariam demande « Aujourd'hui, sur quoi ? » (une seule fois)."""
    local = (at or now()).astimezone(TZ)
    day, weekday = local.date(), str(local.isoweekday())
    asked = []
    async with SessionLocal() as s:
        people = (await s.scalars(select(Member).where(Member.kind == "human", Member.ask_hour.is_not(None)))).all()
        for m in people:
            if weekday not in (m.work_days or "").split(",") or not (m.ask_hour <= local.hour < LAST_ASK_HOUR):
                continue
            if await s.get(TimeAsk, (m.id, day)) is not None:
                continue
            if await s.scalar(select(func.count()).select_from(TimeEntry).where(TimeEntry.member_id == m.id, TimeEntry.day == day)):
                s.add(TimeAsk(member_id=m.id, day=day, state="answered"))
                await s.commit()
                continue
            s.add(TimeAsk(member_id=m.id, day=day, state="asked"))
            await s.commit()
            msg = await post_as_asker(s, m.id, CARD.format(day.isoformat()))
            if msg is not None:
                a = await s.get(TimeAsk, (m.id, day))
                a.message_id = msg.id
                await s.commit()
            asked.append(m.id)
    return asked
