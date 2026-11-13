"""Connexion. En local : on choisit son profil. En ligne : Google (étape suivante)."""
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from itsdangerous import BadSignature, URLSafeSerializer
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import DevLoginIn, MemberOut
from app.config import settings
from app.db import get_session
from app.domain.models import Member

router = APIRouter(prefix="/api/auth", tags=["auth"])
COOKIE = "hq_session"
_signer = URLSafeSerializer(settings.session_secret, salt="hq-session")


async def current_member(request: Request, session: AsyncSession = Depends(get_session)) -> Member:
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
