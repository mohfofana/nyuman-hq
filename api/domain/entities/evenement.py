from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class Evenement:
    """Une ligne du fil de la maison : « Kevin a modifié le document … »."""

    actor_id: int
    verb: str
    text: str
    link: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    id: Optional[int] = None
