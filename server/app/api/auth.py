"""Connexion.

- Humains : en local on choisit son profil ; en ligne, Google (étape suivante).
- Agents : en-tête `X-HQ-Agent` + clé `Authorization: Bearer …` (créée par un head).
  En local seulement (et jamais à travers un tunnel), l'en-tête suffit, comme pour les humains.
"""
import hashlib
import secrets
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from itsdangerous import BadSignature, URLSafeSerializer
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import DevLoginIn, MemberOut
from app.config import settings
from app.db import get_session
from app.domain.models import AgentToken, Member

router = APIRouter(prefix="/api/auth", tags=["auth"])
COOKIE = "hq_session"
_signer = URLSafeSerializer(settings.session_secret, salt="hq-session")


PROXY_HEADERS = ("x-forwarded-for", "cf-connecting-ip", "x-forwarded-host", "forwarded")


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
    response.set_cookie(COOKIE, _signer.dumps(member.id), httponly=True, samesite="lax")
    return member


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
