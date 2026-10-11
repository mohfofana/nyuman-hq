from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import Response

from core.config import settings

COOKIE_NAME = "hq_session"
_ALGORITHM = "HS256"


def create_session_token(membre_id: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {"sub": str(membre_id), "iat": now, "exp": now + timedelta(days=settings.SESSION_DAYS)}
    return jwt.encode(payload, settings.session_secret, algorithm=_ALGORITHM)


def read_session_token(token: str) -> Optional[int]:
    try:
        payload = jwt.decode(token, settings.session_secret, algorithms=[_ALGORITHM])
        return int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        return None


def set_session_cookie(response: Response, membre_id: int) -> None:
    # httpOnly : illisible par le JavaScript de la page. SameSite=Lax : pas envoyé par un autre site sur un POST.
    response.set_cookie(
        COOKIE_NAME,
        create_session_token(membre_id),
        max_age=settings.SESSION_DAYS * 24 * 3600,
        httponly=True,
        samesite="lax",
        secure=settings.ENVIRONMENT == "production",
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(COOKIE_NAME, path="/")
