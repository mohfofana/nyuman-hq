import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


def hash_jeton(jeton: str) -> str:
    """Seule l'empreinte du jeton est gardée en base : un vol de la base ne donne aucun lien utilisable."""
    return hashlib.sha256(jeton.encode()).hexdigest()


@dataclass
class LienConnexion:
    """Un lien de connexion envoyé par email : valable quelques minutes, utilisable une seule fois."""

    membre_id: int
    token_hash: str
    expires_at: datetime
    used_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    id: Optional[int] = None

    def utilisable(self, now: datetime) -> bool:
        return self.used_at is None and now < self.expires_at
