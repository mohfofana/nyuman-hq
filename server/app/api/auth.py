"""Connexion.

- Humains : en local on choisit son profil ; en ligne, c'est Google (seules les adresses de l'équipe passent).
- Agents : en-tête `X-HQ-Agent` + clé `Authorization: Bearer …` (créée par un head).
  En local seulement (et jamais à travers un tunnel), l'en-tête suffit, comme pour les humains.
"""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from itsdangerous import BadSignature, URLSafeSerializer
from sqlalchemy.ext.asyncio import AsyncSession

from pydantic import BaseModel

from app.api.schemas import DevLoginIn, MemberOut
from app.config import Settings, settings
from app import mail
from app.db import get_session
from app.domain.models import AgentToken, Invite, JoinRequest, LoginLink, Member, MemberEmail

router = APIRouter(prefix="/api/auth", tags=["auth"])
COOKIE = "hq_session"
_signer = URLSafeSerializer(settings.session_secret, salt="hq-session")


def read_session(raw: Optional[str]) -> Optional[str]:
    """Lit un cookie de session. À utiliser partout : le signataire change au démarrage,
    donc personne ne doit en garder une copie de son côté."""
    if not raw:
        return None
    try:
        return _signer.loads(raw)
    except BadSignature:
        return None


async def ensure_session_secret() -> None:
    """En ligne, si personne n'a posé de clé, HQ s'en fabrique une et la garde en base.
    Les sessions survivent donc aux redémarrages, sans qu'aucun humain ne touche à la clé."""
    global _signer
    if settings.session_secret != Settings.model_fields["session_secret"].default:
        return
    from app.db import SessionLocal
    from app.domain.models import Setting

    async with SessionLocal() as s:
        row = await s.get(Setting, "session_secret")
        if row is None:
            row = Setting(key="session_secret", value=secrets.token_urlsafe(48))
            s.add(row)
            try:
                await s.commit()
            except Exception:  # deux copies démarrent ensemble : la première a gagné
                await s.rollback()
                row = await s.get(Setting, "session_secret")
        _signer = URLSafeSerializer(row.value, salt="hq-session")


PROXY_HEADERS = ("x-forwarded-for", "cf-connecting-ip", "x-forwarded-host", "forwarded")
STATE_COOKIE = "hq_oauth"
INVITE_COOKIE = "hq_invite"
PENDING_COOKIE = "hq_pending"  # adresse vérifiée par Google, en attente de « qui êtes-vous ? »
INVITE_DAYS = 7
LINK_MINUTES = 20  # durée d'un lien de connexion envoyé par e-mail
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
    member_id = read_session(request.cookies.get(COOKIE))
    if not member_id:
        raise HTTPException(401, "Non connecté")
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


# ---------- connexion par e-mail (lien à usage unique) ----------
class EmailLoginIn(BaseModel):
    email: str


@router.post("/email/request")
async def request_link(body: EmailLoginIn, request: Request, session: AsyncSession = Depends(get_session)):
    """On envoie un lien à l'adresse donnée. On répond toujours pareil : inutile de dire
    qui fait partie de l'équipe à quelqu'un qui essaie des adresses au hasard."""
    email = body.email.strip().lower()
    ok_format = "@" in email and " " not in email and 5 < len(email) < 160 and "." in email.split("@")[-1]
    if ok_format:
        # Pas plus d'un lien toutes les 60 secondes pour une même adresse.
        recent = (await session.scalars(select(LoginLink).where(
            LoginLink.email == email,
            LoginLink.created_at > datetime.now(timezone.utc) - timedelta(seconds=60)))).first()
        if recent is None:
            token = secrets.token_urlsafe(32)
            session.add(LoginLink(token_hash=hash_token(token), email=email,
                                  expires_at=datetime.now(timezone.utc) + timedelta(minutes=LINK_MINUTES)))
            await session.commit()
            base = settings.public_url.rstrip("/") or str(request.base_url).rstrip("/")
            subject, text, html = mail.login_link_message(f"{base}/api/auth/email/{token}", LINK_MINUTES)
            await mail.send(email, subject, text, html)
    return {"sent": True, "minutes": LINK_MINUTES}


@router.get("/email/{token}")
async def use_link(token: str, session: AsyncSession = Depends(get_session)):
    """Le lien reçu par e-mail : il prouve l'adresse, comme Google le ferait."""
    link = await session.get(LoginLink, hash_token(token))
    now_ = datetime.now(timezone.utc)
    if link is None or link.used_at is not None or link.expires_at < now_:
        return back("Ce lien n'est plus valable. Demandez-en un nouveau.")
    link.used_at = now_
    await session.commit()
    member = await member_for(session, link.email)
    if member is None:
        # Adresse inconnue : la personne va dire qui elle est, un responsable confirmera.
        r = RedirectResponse("/rejoindre", status_code=302)
        r.set_cookie(PENDING_COOKIE, _signer.dumps([link.email, ""]), httponly=True, samesite="lax",
                     secure=settings.cookie_secure, max_age=1800)
        return r
    r = RedirectResponse("/accueil", status_code=302)
    set_session(r, member.id)
    return r


# ---------- invitations ----------
@router.post("/invites/{member_id}")
async def create_invite(member_id: str, request: Request, me: Member = Depends(current_member),
                        session: AsyncSession = Depends(get_session)):
    """Un responsable fabrique un lien à envoyer (WhatsApp). La personne s'y connecte avec Google,
    et son adresse se range toute seule sur sa fiche. Un seul usage, 7 jours."""
    if me.kind != "human" or not me.is_head:
        raise HTTPException(403, "Seul un responsable invite quelqu'un")
    member = await session.get(Member, member_id)
    if member is None or member.kind != "human":
        raise HTTPException(404, "Membre inconnu")
    token = secrets.token_urlsafe(32)
    session.add(Invite(token_hash=hash_token(token), member_id=member.id, created_by=me.id,
                       expires_at=datetime.now(timezone.utc) + timedelta(days=INVITE_DAYS)))
    await session.commit()
    base = settings.public_url.rstrip("/") or str(request.base_url).rstrip("/")
    return {"url": f"{base}/api/auth/invite/{token}", "member_id": member.id, "days": INVITE_DAYS}


@router.get("/invite/{token}")
async def use_invite(token: str, session: AsyncSession = Depends(get_session)):
    """La personne clique sur son lien : on le met de côté, puis on l'envoie chez Google."""
    invite = await session.get(Invite, hash_token(token))
    if invite is None or invite.used_at is not None or invite.expires_at < datetime.now(timezone.utc):
        return back("Ce lien d'invitation n'est plus valable. Demandez-en un nouveau.")
    if not google_ready():
        raise HTTPException(503, "La connexion Google n'est pas configurée")
    r = await google_start()
    r.set_cookie(INVITE_COOKIE, _signer.dumps(token), httponly=True, samesite="lax",
                 secure=settings.cookie_secure, max_age=900)
    return r


async def claim_invite(session: AsyncSession, request: Request, email: str) -> Optional[Member]:
    """Au retour de Google, si la personne venait d'une invitation, on lui attache cette adresse."""
    raw = request.cookies.get(INVITE_COOKIE)
    if not raw:
        return None
    try:
        token = _signer.loads(raw)
    except BadSignature:
        return None
    invite = await session.get(Invite, hash_token(token))
    if invite is None or invite.used_at is not None or invite.expires_at < datetime.now(timezone.utc):
        return None
    email = email.strip().lower()
    taken = await session.get(MemberEmail, email)
    if taken is not None and taken.member_id != invite.member_id:
        return None  # cette adresse est déjà celle de quelqu'un d'autre
    if taken is None:
        session.add(MemberEmail(email=email, member_id=invite.member_id, added_by=invite.created_by))
    invite.used_at = datetime.now(timezone.utc)
    await session.commit()
    return await session.get(Member, invite.member_id)


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
    return (await google_identity(code))[0]


async def google_identity(code: str):
    """L'adresse (en minuscules) et le nom tel que Google l'affiche."""
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
    # Toujours en minuscules : c'est la forme rangée en base, et Google n'est pas constant là-dessus.
    return data["email"].strip().lower(), (data.get("name") or "").strip()[:120]


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
        email, seen_name = await google_identity(code)
    except HTTPException:
        raise
    except Exception:
        return back("Google n'a pas répondu, réessayez.")
    member = await claim_invite(session, request, email) or await member_for(session, email)
    if member is None:
        # Adresse inconnue : Google a prouvé qu'elle est bien à cette personne, elle va dire qui elle est.
        r = RedirectResponse("/rejoindre", status_code=302)
        r.set_cookie(PENDING_COOKIE, _signer.dumps([email, seen_name]), httponly=True, samesite="lax",
                     secure=settings.cookie_secure, max_age=1800)
        r.delete_cookie(STATE_COOKIE)
        return r
    r = RedirectResponse("/accueil", status_code=302)
    set_session(r, member.id)
    r.delete_cookie(STATE_COOKIE)
    r.delete_cookie(INVITE_COOKIE)
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


# ---------- se présenter soi-même ----------
def pending_identity(request: Request):
    raw = request.cookies.get(PENDING_COOKIE)
    if not raw:
        raise HTTPException(401, "Connectez-vous d'abord avec Google")
    try:
        email, seen_name = _signer.loads(raw)
    except BadSignature:
        raise HTTPException(401, "Session expirée, reconnectez-vous")
    return email, seen_name


@router.get("/join/me")
async def join_me(request: Request, session: AsyncSession = Depends(get_session)):
    """Après Google, on montre à la personne les fiches encore libres : elle choisit la sienne."""
    email, seen_name = pending_identity(request)
    pending = await session.get(JoinRequest, email)
    taken = set((await session.scalars(select(MemberEmail.member_id))).all())
    free = [m for m in (await session.scalars(select(Member).where(
        Member.kind == "human").order_by(Member.name))).all() if m.id not in taken]
    return {"email": email, "name_seen": seen_name,
            "waiting": pending.member_id if pending else None,
            "candidates": [{"id": m.id, "name": m.name, "title": m.title} for m in free]}


@router.post("/join")
async def join(body: DevLoginIn, request: Request, session: AsyncSession = Depends(get_session)):
    """La personne dit qui elle est. Un responsable confirmera : personne n'entre tout seul."""
    email, seen_name = pending_identity(request)
    if await session.get(MemberEmail, email) is not None:
        raise HTTPException(400, "Cette adresse est déjà rangée sur une fiche")
    member = await session.get(Member, body.member_id)
    if member is None or member.kind != "human":
        raise HTTPException(404, "Membre inconnu")
    if (await session.scalars(select(MemberEmail).where(MemberEmail.member_id == member.id))).first() is not None:
        raise HTTPException(400, "Cette personne a déjà son adresse")
    existing = await session.get(JoinRequest, email)
    if existing is not None:
        existing.member_id = member.id
    else:
        session.add(JoinRequest(email=email, member_id=member.id, name_seen=seen_name))
    await session.commit()
    from app.realtime import hub
    await hub.broadcast({"type": "join.requested", "email": email, "member_id": member.id})
    return {"waiting": member.id, "name": member.name}


@router.get("/profiles")
async def profiles(session: AsyncSession = Depends(get_session)):
    """La liste des noms pour l'écran d'accueil, uniquement quand on entre en cliquant sur son nom."""
    if not settings.dev_login:
        raise HTTPException(404)
    rows = (await session.scalars(select(Member).where(Member.kind == "human").order_by(Member.name))).all()
    return [{"id": m.id, "name": m.name, "title": m.title} for m in rows]


@router.get("/google/status")
async def google_status():
    """L'écran de connexion sait s'il doit proposer Google ou le choix de profil."""
    return {"google": google_ready(), "dev_login": settings.dev_login, "email": mail.configured()}


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

    from app.config import Settings, settings
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
