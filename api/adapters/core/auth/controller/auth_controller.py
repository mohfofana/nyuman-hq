import logging
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.common.providers import get_google_verifier, get_mail_sender
from adapters.core.lien.lien_app_config import LienAppConfig
from adapters.core.membre.contract.membre_view_model import MemberViewModel
from adapters.core.membre.membre_app_config import MembreAppConfig
from core.config import settings
from core.database import get_async_session
from core.session.session_middleware import get_current_membre
from core.session.session_service import clear_session_cookie, set_session_cookie
from domain.entities.membre import Membre
from drivers.utils import public
from use_cases.common.ports.out.google_token_verifier import GoogleTokenVerifier
from use_cases.common.ports.out.mail_sender import MailSender
from use_cases.core.lien.lien_use_cases import EmailLien

logger = logging.getLogger("hq")


class AuthConfigViewModel(BaseModel):
    google_client_id: Optional[str]
    dev_login: bool
    email_login: bool


class GoogleLoginRequest(BaseModel):
    credential: str = Field(min_length=10, max_length=8000)


class DevLoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)


class LienRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)


class ValiderLienRequest(BaseModel):
    jeton: str = Field(min_length=20, max_length=200)


auth_router = APIRouter(prefix="/api/auth", tags=["Connexion"])


@auth_router.get("/config", response_model=AuthConfigViewModel)
@public
async def auth_config(mail_sender: MailSender = Depends(get_mail_sender)) -> AuthConfigViewModel:
    # L'identifiant OAuth Google est public par nature (il est visible dans la page de connexion).
    return AuthConfigViewModel(
        google_client_id=settings.GOOGLE_CLIENT_ID,
        dev_login=settings.dev_login_enabled,
        email_login=mail_sender.configured,
    )


@auth_router.post("/google", response_model=MemberViewModel)
@public
async def login_google(
    request: GoogleLoginRequest,
    response: Response,
    session: AsyncSession = Depends(get_async_session),
    verifier: GoogleTokenVerifier = Depends(get_google_verifier),
) -> MemberViewModel:
    membre = await MembreAppConfig(session, verifier).login_with_google_use_case()(request.credential)
    set_session_cookie(response, membre.id)
    return MemberViewModel.of(membre)


@auth_router.post("/dev", response_model=MemberViewModel)
@public
async def login_dev(
    request: DevLoginRequest,
    response: Response,
    session: AsyncSession = Depends(get_async_session),
) -> MemberViewModel:
    if not settings.dev_login_enabled:
        raise HTTPException(status_code=404, detail="Introuvable.")
    membre = await MembreAppConfig(session).login_dev_use_case()(request.email)
    set_session_cookie(response, membre.id)
    return MemberViewModel.of(membre)


async def _envoyer(mail_sender: MailSender, email: EmailLien) -> None:
    try:
        await mail_sender.send(email.to, email.subject, email.text, email.html)
    except Exception as exc:
        logger.error("Lien de connexion non envoyé (boîte mail) : %s", exc)


@auth_router.post("/lien", status_code=204)
@public
async def demander_lien(
    request: LienRequest,
    background: BackgroundTasks,
    session: AsyncSession = Depends(get_async_session),
    mail_sender: MailSender = Depends(get_mail_sender),
) -> Response:
    if not mail_sender.configured:
        raise HTTPException(status_code=404, detail="Introuvable.")
    email = await LienAppConfig(session).demander_lien_use_case()(request.email)
    if email is not None:
        # Envoi après la réponse : elle arrive aussi vite, que l'adresse ait un compte ou non.
        background.add_task(_envoyer, mail_sender, email)
    return Response(status_code=204, background=background)


@auth_router.post("/lien/valider", response_model=MemberViewModel)
@public
async def valider_lien(
    request: ValiderLienRequest,
    response: Response,
    session: AsyncSession = Depends(get_async_session),
) -> MemberViewModel:
    membre = await LienAppConfig(session).valider_lien_use_case()(request.jeton)
    set_session_cookie(response, membre.id)
    return MemberViewModel.of(membre)


@auth_router.post("/logout", status_code=204)
@public
async def logout(response: Response) -> Response:
    clear_session_cookie(response)
    response.status_code = 204
    return response


@auth_router.get("/me", response_model=MemberViewModel)
async def me(membre: Membre = Depends(get_current_membre)) -> MemberViewModel:
    return MemberViewModel.of(membre)
