"""Chiffres de l'app Nyuman (totaux seulement) lus sur nyuman-api, gardés 5 minutes en mémoire.

Sans HQ_STATS_URL / HQ_STATS_KEY, on répond « pas encore branché » et les cartes affichent « bientôt ».
"""
from __future__ import annotations

import time
from typing import Optional

import httpx
from fastapi import APIRouter, Depends

from app.api.auth import current_member
from app.config import settings
from app.domain.models import Member

router = APIRouter(prefix="/api", tags=["app-stats"])
CACHE_S = 300
_cache: dict = {"at": 0.0, "data": None}


async def fetch_stats() -> dict:
    async with httpx.AsyncClient(timeout=8) as c:
        r = await c.get(settings.stats_url, headers={"X-HQ-Stats-Key": settings.stats_key})
        r.raise_for_status()
        return r.json()


@router.get("/app-stats")
async def app_stats(_me: Member = Depends(current_member)):
    if not settings.stats_url or not settings.stats_key:
        return {"available": False, "reason": "not_configured"}
    if _cache["data"] is not None and time.time() - _cache["at"] < CACHE_S:
        return {"available": True, "stats": _cache["data"]}
    try:
        data = await fetch_stats()
    except Exception as e:  # API injoignable ou clé refusée : on garde le dernier chiffre connu s'il existe
        code = getattr(getattr(e, "response", None), "status_code", None)
        print(f"chiffres de l'app : échec ({code or type(e).__name__})")  # jamais la clé dans le journal
        if _cache["data"] is not None:
            return {"available": True, "stale": True, "stats": _cache["data"]}
        return {"available": False, "reason": "unreachable"}
    _cache.update(at=time.time(), data=data)
    return {"available": True, "stats": data}


def reset_cache(data: Optional[dict] = None) -> None:
    _cache.update(at=time.time() if data else 0.0, data=data)
