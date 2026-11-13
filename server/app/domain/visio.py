"""Création des liens de visio.

- Jitsi : gratuit, sans compte côté HQ ; lien unique et difficile à deviner.
- Google Meet : passe par l'API Google Calendar avec le compte Google de l'équipe.
  Pas encore branché : il faut les identifiants Google (Kevin, voir docs/demande-kevin-mise-en-ligne.md).
"""
from __future__ import annotations

import re
import secrets
import unicodedata

from app.config import settings


class VisioUnavailable(Exception):
    pass


def _slug(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    words = re.findall(r"[A-Za-z0-9]+", text)[:5]
    return "".join(w.capitalize() for w in words) or "Reunion"


def jitsi_link(title: str) -> str:
    return f"{settings.jitsi_base.rstrip('/')}/Nyuman-{_slug(title)}-{secrets.token_hex(5)}"


def google_meet_ready() -> bool:
    return bool(settings.google_client_id and settings.google_client_secret and settings.google_refresh_token)


async def meet_link(title: str, start, end, attendee_emails) -> str:  # pragma: no cover - branché plus tard
    if not google_meet_ready():
        raise VisioUnavailable("Google Meet n'est pas encore branché (identifiants Google manquants).")
    raise VisioUnavailable("Google Meet : branchement prévu à la mise en ligne.")


def make_link(kind: str, title: str) -> str:
    if kind == "jitsi":
        return jitsi_link(title)
    if kind == "none":
        return ""
    raise VisioUnavailable("Google Meet n'est pas encore branché : choisissez Jitsi pour l'instant.")
