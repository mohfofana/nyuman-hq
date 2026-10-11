from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional

# Les pièces de la maison où un humain peut se trouver (la page qu'il a ouverte).
PIECES = ("salon", "bureaux", "bibliotheque", "projet", "conseil", "entree")


@dataclass
class Presence:
    piece: str = "salon"
    label: str = "est dans le salon"
    document_id: Optional[int] = None
    editing: bool = False
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["updated_at"] = self.updated_at.isoformat()
        return data


class PresenceRegistry:
    """Où est chacun en ce moment. Éphémère : rien n'est écrit en base, tout repart à zéro au redémarrage."""

    def __init__(self) -> None:
        self._presences: Dict[int, Presence] = {}
        self._connections: Dict[int, int] = {}

    def connect(self, membre_id: int) -> Presence:
        self._connections[membre_id] = self._connections.get(membre_id, 0) + 1
        return self._presences.setdefault(membre_id, Presence())

    def disconnect(self, membre_id: int) -> bool:
        """Renvoie True si le membre n'a plus aucun écran ouvert (il a quitté la maison)."""
        remaining = self._connections.get(membre_id, 0) - 1
        if remaining > 0:
            self._connections[membre_id] = remaining
            return False
        self._connections.pop(membre_id, None)
        self._presences.pop(membre_id, None)
        return True

    def update(self, membre_id: int, piece: str, label: str, document_id: Optional[int], editing: bool) -> Presence:
        presence = Presence(piece=piece, label=label, document_id=document_id, editing=editing)
        self._presences[membre_id] = presence
        return presence

    def snapshot(self) -> Dict[int, Presence]:
        return {mid: p for mid, p in self._presences.items() if self._connections.get(mid, 0) > 0}

    def clear(self) -> None:
        self._presences.clear()
        self._connections.clear()


presence_registry = PresenceRegistry()
