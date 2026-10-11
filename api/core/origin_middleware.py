from typing import Iterable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

_SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


class OriginCheckMiddleware(BaseHTTPMiddleware):
    """Refuse une écriture venue d'un autre site (protection CSRF en plus du cookie SameSite=Lax)."""

    def __init__(self, app, allowed_origins: Iterable[str]):
        super().__init__(app)
        self._allowed = set(allowed_origins)

    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("origin")
        if request.method not in _SAFE_METHODS and origin:
            same_origin = origin.rstrip("/") == f"{request.url.scheme}://{request.url.netloc}"
            if not same_origin and origin.rstrip("/") not in self._allowed:
                return JSONResponse(status_code=403, content={"detail": "Origine non autorisée."})
        return await call_next(request)
