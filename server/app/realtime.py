"""Temps réel : connexions WebSocket, présence automatique, diffusion d'événements.

Tout tient en mémoire dans le serveur (une seule instance suffit pour l'équipe).
"""
from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import Dict, Iterable, Optional

from fastapi import WebSocket


def now() -> datetime:
    return datetime.now(timezone.utc)


class Hub:
    def __init__(self) -> None:
        # membre -> {connexion: "active" | "idle"}
        self.conns: Dict[str, Dict[WebSocket, str]] = {}
        self.last_seen: Dict[str, datetime] = {}
        # membres « En réunion » (calculé par le planificateur des réunions)
        self.in_meeting: set = set()
        self._lock = asyncio.Lock()

    # ----- présence -----
    def snapshot(self, member_id: str) -> dict:
        states = list(self.conns.get(member_id, {}).values())
        last = self.last_seen.get(member_id)
        return {
            "member_id": member_id,
            "connected": bool(states),
            "idle": bool(states) and all(s == "idle" for s in states),
            "in_meeting": member_id in self.in_meeting,
            "last_seen": last.isoformat() if last else None,
        }

    def all_snapshots(self, known: Iterable[str]) -> list:
        return [self.snapshot(m) for m in known]

    async def connect(self, member_id: str, ws: WebSocket) -> None:
        async with self._lock:
            self.conns.setdefault(member_id, {})[ws] = "active"
            self.last_seen[member_id] = now()
        await self.broadcast({"type": "presence", **self.snapshot(member_id)})

    async def disconnect(self, member_id: str, ws: WebSocket) -> None:
        async with self._lock:
            self.conns.get(member_id, {}).pop(ws, None)
            if not self.conns.get(member_id):
                self.conns.pop(member_id, None)
            self.last_seen[member_id] = now()
        await self.broadcast({"type": "presence", **self.snapshot(member_id)})

    async def set_state(self, member_id: str, ws: WebSocket, state: str) -> None:
        if state not in ("active", "idle"):
            return
        before = self.snapshot(member_id)
        self.conns.get(member_id, {})[ws] = state
        if state == "active":
            self.last_seen[member_id] = now()
        after = self.snapshot(member_id)
        if (before["connected"], before["idle"]) != (after["connected"], after["idle"]):
            await self.broadcast({"type": "presence", **after})

    def touch(self, member_id: str) -> None:
        """Un agent (sans WebSocket) qui agit compte comme vu à l'instant."""
        self.last_seen[member_id] = now()

    # ----- diffusion -----
    async def broadcast(self, event: dict, to: Optional[Iterable[str]] = None, exclude: Optional[str] = None) -> None:
        data = json.dumps(event, default=str)
        targets = set(to) if to is not None else set(self.conns)
        for member_id in targets:
            if member_id == exclude:
                continue
            for ws in list(self.conns.get(member_id, {})):
                try:
                    await ws.send_text(data)
                except Exception:  # connexion morte : on l'oublie
                    self.conns.get(member_id, {}).pop(ws, None)


hub = Hub()
