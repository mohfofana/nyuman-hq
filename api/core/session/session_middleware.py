from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.core.membre.membre_app_config import MembreAppConfig
from core.database import get_async_session
from core.session.session_service import COOKIE_NAME, read_session_token
from domain.entities.membre import HUMAIN, Membre


async def get_current_membre(request: Request, session: AsyncSession = Depends(get_async_session)) -> Membre:
    """Le membre connecté. Relu en base à chaque requête : un accès retiré par un head coupe la session tout de suite."""
    token = request.cookies.get(COOKIE_NAME)
    membre_id = read_session_token(token) if token else None
    if membre_id is None:
        raise HTTPException(status_code=401, detail="Connecte-toi pour entrer dans la maison.")

    config = MembreAppConfig(session)
    membre = await config.get_membre_by_id_use_case()(membre_id)
    if membre is None or membre.kind != HUMAIN or not membre.active:
        raise HTTPException(status_code=401, detail="Ta session n’est plus valable. Reconnecte-toi.")
    return await config.mark_presence_use_case()(membre)
