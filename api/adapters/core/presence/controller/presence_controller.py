import asyncio
import json
from typing import Any, AsyncIterator, Dict, Literal, Optional

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from core.realtime.broker import Broker, broker
from core.realtime.presence import PresenceRegistry, presence_registry
from core.session.session_middleware import get_current_membre
from domain.entities.membre import Membre

PING_SECONDES = 20

presence_router = APIRouter(prefix="/api", tags=["En direct"])


class PresenceRequest(BaseModel):
    piece: Literal["salon", "bureaux", "bibliotheque", "projet", "conseil", "entree"]
    label: str = Field(min_length=1, max_length=160)
    document_id: Optional[int] = None
    editing: bool = False


def _sse(message: Dict[str, Any]) -> str:
    return f"data: {json.dumps(message, ensure_ascii=False)}\n\n"


def _presence_message(membre_id: int, registry: PresenceRegistry) -> Dict[str, Any]:
    presence = registry.snapshot().get(membre_id)
    return {"type": "presence", "membre_id": membre_id, "presence": presence.to_dict() if presence else None}


async def live_stream(
    membre_id: int,
    registry: PresenceRegistry,
    bus: Broker,
    is_disconnected,
    ping_seconds: float = PING_SECONDES,
) -> AsyncIterator[str]:
    """Le flux d'un écran : l'état de la maison à l'arrivée, puis chaque changement, et un signe de vie régulier."""
    # On annonce l'arrivée aux autres avant de s'abonner : cet écran la reçoit déjà dans « bonjour ».
    registry.connect(membre_id)
    bus.publish(_presence_message(membre_id, registry))
    queue = bus.subscribe()
    try:
        snapshot = {str(mid): p.to_dict() for mid, p in registry.snapshot().items()}
        yield _sse({"type": "bonjour", "presences": snapshot})
        while not await is_disconnected():
            try:
                message = await asyncio.wait_for(queue.get(), timeout=ping_seconds)
                yield _sse(message)
            except asyncio.TimeoutError:
                yield ": ping\n\n"
    finally:
        bus.unsubscribe(queue)
        if registry.disconnect(membre_id):
            bus.publish({"type": "presence", "membre_id": membre_id, "presence": None})


@presence_router.get("/flux")
async def flux(request: Request, membre: Membre = Depends(get_current_membre)) -> StreamingResponse:
    return StreamingResponse(
        live_stream(membre.id, presence_registry, broker, request.is_disconnected),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@presence_router.post("/presence", status_code=204)
async def report_presence(request: PresenceRequest, membre: Membre = Depends(get_current_membre)) -> Response:
    presence_registry.update(membre.id, request.piece, request.label.strip(), request.document_id, request.editing)
    broker.publish(_presence_message(membre.id, presence_registry))
    return Response(status_code=204)
