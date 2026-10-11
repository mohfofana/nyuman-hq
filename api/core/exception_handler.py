import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from core.exceptions import BusinessException, ErrorType

logger = logging.getLogger("hq")

_STATUS = {
    ErrorType.NOT_FOUND: 404,
    ErrorType.ALREADY_EXISTS: 409,
    ErrorType.CONFLICT: 409,
    ErrorType.VALIDATION_ERROR: 400,
    ErrorType.UNAUTHORIZED: 401,
    ErrorType.FORBIDDEN: 403,
}


def setup_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(BusinessException)
    async def _business(_: Request, exc: BusinessException) -> JSONResponse:
        return JSONResponse(
            status_code=_STATUS.get(exc.error_type, 500),
            content={"detail": exc.message, "error_type": exc.error_type.value},
        )

    @app.exception_handler(Exception)
    async def _unexpected(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Erreur inattendue sur %s %s", request.method, request.url.path)
        return JSONResponse(status_code=500, content={"detail": "Erreur inattendue du serveur."})
