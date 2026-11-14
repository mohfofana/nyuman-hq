"""Connexion.

- Humains : en local on choisit son profil ; en ligne, c'est Google (seules les adresses de l'équipe passent).
- Agents : en-tête `X-HQ-Agent` + clé `Authorization: Bearer …` (créée par un head).
  En local seulement (et jamais à travers un tunnel), l'en-tête suffit, comme pour les humains.
"""
import hashlib
import secrets
from typing import Optional
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from itsdangerous import BadSignature, URLSafeSerializer
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import DevLoginIn, MemberOut
from app.config import settings
from app.db import get_session
from app.domain.models import AgentToken, Member, MemberEmail

router = APIRouter(prefix="/api/auth", tags=["auth"])
COOKIE = "hq_session"
_signer = URLSafeSerializer(settings.session_secret, salt="hq-session")


PROXY_HEADERS = ("x-forwarded-for", "cf-connecting-ip", "x-forwarded-host", "forwarded")
STATE_COOKIE = "hq_oauth"
GOOGLE_AUTH = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO = "https://www.googleapis.com/oauth2/v3/userinfo"


def set_session(response: Response, member_id: str) -> None:
    response.set_cookie(COOKIE, _signer.dumps(member_id), httponly=True, samesite="lax",
                        secure=settings.cookie_secure, max_age=60 * 60 * 24 * 30)


def redirect_uri() -> str:
    return settings.public_url.rstrip("/") + "/api/auth/google/callback"


def google_ready() -> bool:
    return bool(settings.google_client_id and settings.google_client_secret and settings.public_url)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _direct_local(request: Request) -> bool:
    host = request.client.host if request.client else ""
    return host in ("127.0.0.1", "::1") and not any(h in request.headers for h in PROXY_HEADERS)


async def _agent(request: Request, session: AsyncSession, agent_id: str) -> Member:
    from app.realtime import hub

    member = await session.get(Member, agent_id)
    if member is None or member.kind != "agent":
        raise HTTPException(401, "Agent inconnu")
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        row = await session.get(AgentToken, hash_token(auth[7:].strip()))
        if row is None or row.member_id != member.id:
            raise HTTPException(401, "Clé d'agent invalide")
    elif not (settings.dev_login and _direct_local(request)):
        raise HTTPException(401, "Clé d'agent requise")
    hub.touch(member.id)
    return member


async def current_member(request: Request, session: AsyncSession = Depends(get_session)) -> Member:
    agent_id = request.headers.get("x-hq-agent")
    if agent_id:
        return await _agent(request, session, agent_id)
    raw = request.cookies.get(COOKIE)
    if not raw:
        raise HTTPException(401, "Non connecté")
    try:
        member_id = _signer.loads(raw)
    except BadSignature:
        raise HTTPException(401, "Session invalide")
    member = await session.get(Member, member_id)
    if member is None:
        raise HTTPException(401, "Membre inconnu")
    return member


@router.post("/dev-login", response_model=MemberOut)
async def dev_login(body: DevLoginIn, response: Response, session: AsyncSession = Depends(get_session)):
    if not settings.dev_login:
        raise HTTPException(404)
    member = await session.get(Member, body.member_id)
    if member is None or member.kind != "human":
        raise HTTPException(400, "Choisissez un membre humain")
    set_session(response, member.id)
    return member


# ---------- connexion Google ----------
@router.get("/google/start")
async def google_start():
    """Envoie vers Google. Au retour, HQ reconnaît la personne à son adresse."""
    if not google_ready():
        raise HTTPException(503, "La connexion Google n'est pas configurée")
    state = secrets.token_urlsafe(24)
    url = GOOGLE_AUTH + "?" + urlencode({
        "client_id": settings.google_client_id, "redirect_uri": redirect_uri(), "response_type": "code",
        "scope": "openid email profile", "state": state, "prompt": "select_account"})
    r = RedirectResponse(url, status_code=302)
    r.set_cookie(STATE_COOKIE, _signer.dumps(state), httponly=True, samesite="lax",
                 secure=settings.cookie_secure, max_age=600)
    return r


async def google_email(code: str) -> str:
    async with httpx.AsyncClient(timeout=10) as c:
        tok = await c.post(GOOGLE_TOKEN, data={
            "code": code, "client_id": settings.google_client_id, "client_secret": settings.google_client_secret,
            "redirect_uri": redirect_uri(), "grant_type": "authorization_code"})
        tok.raise_for_status()
        access = tok.json().get("access_token", "")
        info = await c.get(GOOGLE_USERINFO, headers={"Authorization": f"Bearer {access}"})
        info.raise_for_status()
    data = info.json()
    if not data.get("email") or not data.get("email_verified"):
        raise HTTPException(403, "Adresse Google non vérifiée")
    return data["email"]


def back(message: str) -> RedirectResponse:
    """Retour à l'écran de connexion, avec un mot à afficher."""
    return RedirectResponse("/?" + urlencode({"erreur": message}), status_code=302)


@router.get("/google/callback")
async def google_callback(request: Request, state: str = "", code: str = "", error: str = "",
                          session: AsyncSession = Depends(get_session)):
    if not google_ready():
        raise HTTPException(503, "La connexion Google n'est pas configurée")
    if error or not code:
        return back("Connexion annulée.")
    raw = request.cookies.get(STATE_COOKIE)
    try:
        if not raw or _signer.loads(raw) != state:
            raise BadSignature("state")
    except BadSignature:
        return back("Lien de connexion expiré, réessayez.")
    try:
        email = await google_email(code)
    except HTTPException:
        raise
    except Exception:
        return back("Google n'a pas répondu, réessayez.")
    member = await member_for(session, email)
    if member is None:
        return back("Cette adresse ne fait pas partie de l'équipe. Demandez à un responsable de l'ajouter.")
    r = RedirectResponse("/accueil", status_code=302)
    set_session(r, member.id)
    r.delete_cookie(STATE_COOKIE)
    return r


async def member_for(session: AsyncSession, email: str) -> Optional[Member]:
    """Qui se cache derrière cette adresse ? N'importe laquelle de ses adresses fait l'affaire."""
    email = email.strip().lower()
    row = await session.get(MemberEmail, email)
    if row is not None:
        member = await session.get(Member, row.member_id)
        if member is not None and member.kind == "human":
            return member
    # Première connexion : une adresse de secours posée par Kevin, le temps de remplir les fiches.
    for pair in settings.bootstrap_emails.split(","):
        if "=" in pair:
            addr, mid = (x.strip().lower() for x in pair.split("=", 1))
            if addr == email:
                member = await session.get(Member, mid)
                if member is not None and member.kind == "human":
                    return member
    return None


@router.get("/google/status")
async def google_status():
    """L'écran de connexion sait s'il doit proposer Google ou le choix de profil."""
    return {"google": google_ready(), "dev_login": settings.dev_login}


@router.post("/logout", status_code=204)
async def logout(response: Response):
    response.delete_cookie(COOKIE)


@router.get("/me", response_model=MemberOut)
async def me(member: Member = Depends(current_member)):
    return member


@router.post("/agents/{agent_id}/token")
async def new_agent_token(agent_id: str, me: Member = Depends(current_member), session: AsyncSession = Depends(get_session)):
    """Un head crée la clé d'un agent. Elle n'est montrée qu'une fois ; HQ n'en garde que l'empreinte."""
    if me.kind != "human" or not me.is_head:
        raise HTTPException(403, "Seul un head crée la clé d'un agent")
    agent = await session.get(Member, agent_id)
    if agent is None or agent.kind != "agent":
        raise HTTPException(404, "Agent inconnu")
    token = "hqa_" + secrets.token_urlsafe(32)
    session.add(AgentToken(token_hash=hash_token(token), member_id=agent.id, created_by=me.id))
    await session.commit()
    return {"agent_id": agent.id, "token": token}


@router.post("/agents/{agent_id}/wake")
async def wake_agent(agent_id: str, message_id: str, me: Member = Depends(current_member),
                     session: AsyncSession = Depends(get_session)):
    """Relancer un agent sur un message qu'il n'a pas encore traité (réservé aux heads)."""
    from app.domain.models import Channel, ChannelMember, Message
    from app.wake import waker

    if me.kind != "human" or not me.is_head:
        raise HTTPException(403, "Réservé aux heads")
    agent = await session.get(Member, agent_id)
    msg = await session.get(Message, message_id)
    if agent is None or agent.kind != "agent" or msg is None:
        raise HTTPException(404)
    ch = await session.get(Channel, msg.channel_id)
    if ch.kind == "dm" and await session.get(ChannelMember, (ch.id, agent_id)) is None:
        raise HTTPException(400, "L'agent n'est pas dans cette discussion")
    author = await session.get(Member, msg.author_id)
    woken = await waker.on_message(msg, ch, author, {agent_id})
    return {"woken": woken}


@router.get("/agents/runs")
async def agent_runs_summary(_me: Member = Depends(current_member), session: AsyncSession = Depends(get_session)):
    """Compteur visible : réveils du jour, coût du mois, dernier état, par agent."""
    from datetime import datetime, timezone

    from sqlalchemy import func, select

    from app.config import settings
    from app.domain.models import AgentRun

    now_ = datetime.now(timezone.utc)
    day = now_.replace(hour=0, minute=0, second=0, microsecond=0)
    month = day.replace(day=1)
    out = {}
    agents = (await session.scalars(select(Member.id).where(Member.kind == "agent"))).all()
    for a in agents:
        today = await session.scalar(select(func.count()).select_from(AgentRun).where(
            AgentRun.agent_id == a, AgentRun.created_at >= day, AgentRun.status.in_(["running", "done"]))) or 0
        cost = await session.scalar(select(func.coalesce(func.sum(AgentRun.cost_usd), 0)).where(
            AgentRun.agent_id == a, AgentRun.created_at >= month)) or 0
        last = await session.scalar(select(AgentRun).where(AgentRun.agent_id == a).order_by(AgentRun.created_at.desc()).limit(1))
        out[a] = {"today": today, "cap": settings.agent_daily_cap, "month_cost_usd": round(float(cost), 3),
                  "last_status": last.status if last else None, "last_at": last.created_at if last else None,
                  "last_error": (last.error[:160] if last and last.status == "failed" else "")}
    return {"enabled": settings.agent_wake, "agents": out}
