"""Projets façon Notion : projets, pages (documents riches), tâches avec responsable, échéance et statut."""
from __future__ import annotations

from datetime import date, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import current_member
from app.db import get_session
from app.domain.models import Member, Page, Project, Task
from app.realtime import hub, now

router = APIRouter(prefix="/api", tags=["projects"])
STATUSES = ("todo", "doing", "review", "done")
PRIORITIES = ("low", "normal", "high")


# ---------- schémas ----------
class ProjectIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    icon: str = Field(default="📁", max_length=16)
    description: str = Field(default="", max_length=2000)
    department: str = Field(default="", max_length=60)
    owner_id: Optional[str] = None


class ProjectPatch(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    icon: Optional[str] = Field(default=None, max_length=16)
    description: Optional[str] = Field(default=None, max_length=2000)
    department: Optional[str] = Field(default=None, max_length=60)
    owner_id: Optional[str] = None
    archived: Optional[bool] = None


class PageIn(BaseModel):
    title: str = Field(default="", max_length=200)
    icon: str = Field(default="📄", max_length=16)
    parent_id: Optional[str] = None
    content: str = Field(default="", max_length=2_000_000)
    text: str = Field(default="", max_length=500_000)


class PagePatch(BaseModel):
    title: Optional[str] = Field(default=None, max_length=200)
    icon: Optional[str] = Field(default=None, max_length=16)
    content: Optional[str] = Field(default=None, max_length=2_000_000)
    text: Optional[str] = Field(default=None, max_length=500_000)
    parent_id: Optional[str] = None
    archived: Optional[bool] = None


class TaskIn(BaseModel):
    project_id: str
    title: str = Field(min_length=1, max_length=300)
    description: str = Field(default="", max_length=10000)
    status: str = "todo"
    priority: str = "normal"
    assignee_id: Optional[str] = None
    due_date: Optional[date] = None
    page_id: Optional[str] = None


class TaskPatch(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=300)
    description: Optional[str] = Field(default=None, max_length=10000)
    status: Optional[str] = None
    priority: Optional[str] = None
    assignee_id: Optional[str] = None
    due_date: Optional[date] = None
    project_id: Optional[str] = None
    position: Optional[float] = None
    archived: Optional[bool] = None


# ---------- sérialisation ----------
def project_out(p: Project, counts: Optional[dict] = None) -> dict:
    return {"id": p.id, "name": p.name, "icon": p.icon, "description": p.description, "department": p.department,
            "owner_id": p.owner_id, "created_by": p.created_by, "archived": p.archived, "created_at": p.created_at,
            "counts": counts or {}}


def page_out(p: Page, full: bool = False) -> dict:
    d = {"id": p.id, "project_id": p.project_id, "parent_id": p.parent_id, "title": p.title, "icon": p.icon,
         "position": p.position, "archived": p.archived, "created_by": p.created_by, "updated_by": p.updated_by,
         "created_at": p.created_at, "updated_at": p.updated_at}
    if full:
        d["content"] = p.content
        d["text"] = p.text
    return d


def task_out(t: Task) -> dict:
    return {"id": t.id, "project_id": t.project_id, "title": t.title, "description": t.description, "status": t.status,
            "priority": t.priority, "assignee_id": t.assignee_id, "due_date": t.due_date, "page_id": t.page_id,
            "position": t.position, "archived": t.archived, "created_by": t.created_by, "updated_by": t.updated_by,
            "created_at": t.created_at, "updated_at": t.updated_at, "completed_at": t.completed_at}


async def project_or_404(session: AsyncSession, pid: str) -> Project:
    p = await session.get(Project, pid)
    if p is None:
        raise HTTPException(404, "Projet introuvable")
    return p


async def check_member(session: AsyncSession, mid: Optional[str]) -> None:
    if mid and await session.get(Member, mid) is None:
        raise HTTPException(400, "Membre inconnu")


# ---------- projets ----------
@router.get("/projects")
async def list_projects(archived: bool = False, _me: Member = Depends(current_member), session: AsyncSession = Depends(get_session)):
    rows = (await session.scalars(select(Project).where(Project.archived.is_(archived)).order_by(Project.created_at))).all()
    counts = {}
    for pid, status, n in (await session.execute(select(Task.project_id, Task.status, func.count()).where(
            Task.archived.is_(False)).group_by(Task.project_id, Task.status))).all():
        counts.setdefault(pid, {})[status] = n
    return [project_out(p, counts.get(p.id, {})) for p in rows]


@router.post("/projects", status_code=201)
async def create_project(body: ProjectIn, me: Member = Depends(current_member), session: AsyncSession = Depends(get_session)):
    await check_member(session, body.owner_id)
    p = Project(name=body.name.strip(), icon=body.icon or "📁", description=body.description.strip(),
                department=body.department, owner_id=body.owner_id or me.id, created_by=me.id)
    session.add(p)
    await session.commit()
    await hub.broadcast({"type": "project.updated", "project_id": p.id})
    return project_out(p)


@router.patch("/projects/{pid}")
async def update_project(pid: str, body: ProjectPatch, me: Member = Depends(current_member), session: AsyncSession = Depends(get_session)):
    p = await project_or_404(session, pid)
    data = body.model_dump(exclude_unset=True)
    await check_member(session, data.get("owner_id"))
    for k, v in data.items():
        setattr(p, k, v.strip() if isinstance(v, str) else v)
    await session.commit()
    await hub.broadcast({"type": "project.updated", "project_id": p.id})
    return project_out(p)


@router.get("/projects/{pid}/pages")
async def list_pages(pid: str, _me: Member = Depends(current_member), session: AsyncSession = Depends(get_session)):
    await project_or_404(session, pid)
    rows = (await session.scalars(select(Page).where(Page.project_id == pid, Page.archived.is_(False))
                                  .order_by(Page.position, Page.created_at))).all()
    return [page_out(p) for p in rows]


# ---------- pages ----------
@router.post("/projects/{pid}/pages", status_code=201)
async def create_page(pid: str, body: PageIn, me: Member = Depends(current_member), session: AsyncSession = Depends(get_session)):
    await project_or_404(session, pid)
    if body.parent_id:
        parent = await session.get(Page, body.parent_id)
        if parent is None or parent.project_id != pid:
            raise HTTPException(400, "Page parente introuvable")
    last = await session.scalar(select(func.max(Page.position)).where(Page.project_id == pid))
    p = Page(project_id=pid, parent_id=body.parent_id, title=body.title.strip(), icon=body.icon or "📄",
             content=body.content, text=body.text, position=(last or 0) + 1, created_by=me.id, updated_by=me.id,
             updated_at=now())
    session.add(p)
    await session.commit()
    await hub.broadcast({"type": "page.updated", "page_id": p.id, "project_id": pid, "by": me.id})
    return page_out(p, full=True)


@router.get("/pages/{page_id}")
async def get_page(page_id: str, _me: Member = Depends(current_member), session: AsyncSession = Depends(get_session)):
    p = await session.get(Page, page_id)
    if p is None:
        raise HTTPException(404, "Page introuvable")
    return page_out(p, full=True)


@router.patch("/pages/{page_id}")
async def update_page(page_id: str, body: PagePatch, me: Member = Depends(current_member), session: AsyncSession = Depends(get_session)):
    p = await session.get(Page, page_id)
    if p is None:
        raise HTTPException(404, "Page introuvable")
    data = body.model_dump(exclude_unset=True)
    if data.get("parent_id"):
        if data["parent_id"] == p.id:
            raise HTTPException(400, "Une page ne peut pas être dans elle-même")
        parent = await session.get(Page, data["parent_id"])
        if parent is None or parent.project_id != p.project_id:
            raise HTTPException(400, "Page parente introuvable")
    for k, v in data.items():
        setattr(p, k, v)
    p.updated_by, p.updated_at = me.id, now()
    await session.commit()
    await hub.broadcast({"type": "page.updated", "page_id": p.id, "project_id": p.project_id, "by": me.id})
    return page_out(p, full=True)


# ---------- tâches ----------
@router.get("/tasks")
async def list_tasks(project_id: Optional[str] = None, assignee_id: Optional[str] = None, status: Optional[str] = None,
                     done_since_days: Optional[int] = None, _me: Member = Depends(current_member),
                     session: AsyncSession = Depends(get_session)):
    q = select(Task).where(Task.archived.is_(False))
    if project_id:
        q = q.where(Task.project_id == project_id)
    if assignee_id:
        q = q.where(Task.assignee_id == assignee_id)
    if status:
        q = q.where(Task.status.in_(status.split(",")))
    if done_since_days is not None:
        q = q.where(Task.status == "done", Task.completed_at >= now() - timedelta(days=done_since_days))
    rows = (await session.scalars(q.order_by(Task.position, Task.created_at))).all()
    return [task_out(t) for t in rows]


def check_task_fields(data: dict) -> None:
    if "status" in data and data["status"] not in STATUSES:
        raise HTTPException(400, "Statut inconnu")
    if "priority" in data and data["priority"] not in PRIORITIES:
        raise HTTPException(400, "Priorité inconnue")


@router.post("/tasks", status_code=201)
async def create_task(body: TaskIn, me: Member = Depends(current_member), session: AsyncSession = Depends(get_session)):
    await project_or_404(session, body.project_id)
    data = body.model_dump()
    check_task_fields(data)
    await check_member(session, body.assignee_id)
    last = await session.scalar(select(func.max(Task.position)).where(Task.project_id == body.project_id))
    t = Task(**{**data, "title": body.title.strip()}, position=(last or 0) + 1, created_by=me.id, updated_by=me.id,
             updated_at=now(), completed_at=now() if body.status == "done" else None)
    session.add(t)
    await session.commit()
    await hub.broadcast({"type": "task.updated", "task": task_out(t), "by": me.id})
    if t.assignee_id and t.assignee_id != me.id:
        await hub.broadcast({"type": "task.assigned", "task": task_out(t), "by": me.id}, to=[t.assignee_id])
    return task_out(t)


@router.patch("/tasks/{task_id}")
async def update_task(task_id: str, body: TaskPatch, me: Member = Depends(current_member), session: AsyncSession = Depends(get_session)):
    t = await session.get(Task, task_id)
    if t is None:
        raise HTTPException(404, "Tâche introuvable")
    data = body.model_dump(exclude_unset=True)
    check_task_fields(data)
    await check_member(session, data.get("assignee_id"))
    if data.get("project_id"):
        await project_or_404(session, data["project_id"])
    before_assignee = t.assignee_id
    if "status" in data and data["status"] != t.status:
        t.completed_at = now() if data["status"] == "done" else None
    for k, v in data.items():
        setattr(t, k, v.strip() if isinstance(v, str) and k == "title" else v)
    t.updated_by, t.updated_at = me.id, now()
    await session.commit()
    await hub.broadcast({"type": "task.updated", "task": task_out(t), "by": me.id})
    if t.assignee_id and t.assignee_id != before_assignee and t.assignee_id != me.id:
        await hub.broadcast({"type": "task.assigned", "task": task_out(t), "by": me.id}, to=[t.assignee_id])
    return task_out(t)


@router.get("/projects-search")
async def search_projects(q: str, _me: Member = Depends(current_member), session: AsyncSession = Depends(get_session)):
    """Recherche dans les titres et le texte des pages, et dans les tâches."""
    q = q.strip()
    if len(q) < 2:
        return {"pages": [], "tasks": []}
    pat = "%" + q.replace("%", r"\%").replace("_", r"\_") + "%"
    pages = (await session.scalars(select(Page).where(Page.archived.is_(False), or_(Page.title.ilike(pat), Page.text.ilike(pat))).limit(20))).all()
    tasks = (await session.scalars(select(Task).where(Task.archived.is_(False), or_(Task.title.ilike(pat), Task.description.ilike(pat))).limit(20))).all()
    return {"pages": [page_out(p) for p in pages], "tasks": [task_out(t) for t in tasks]}
