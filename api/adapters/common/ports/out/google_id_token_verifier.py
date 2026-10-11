from typing import Optional

from fastapi.concurrency import run_in_threadpool
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from use_cases.common.ports.out.google_token_verifier import GoogleIdentity, GoogleTokenVerifier
from use_cases.core.membre.exceptions.membre_exceptions import ConnexionGoogleInvalideException


class GoogleIdTokenVerifier(GoogleTokenVerifier):
    """Vérifie la signature Google, le destinataire (notre identifiant OAuth) et l'expiration du jeton."""

    def __init__(self, client_id: Optional[str]):
        self._client_id = client_id
        self._request = google_requests.Request()

    async def verify(self, credential: str) -> GoogleIdentity:
        if not self._client_id:
            raise ConnexionGoogleInvalideException()
        try:
            info = await run_in_threadpool(id_token.verify_oauth2_token, credential, self._request, self._client_id)
        except ValueError:
            raise ConnexionGoogleInvalideException()
        if not info.get("email") or not info.get("email_verified"):
            raise ConnexionGoogleInvalideException()
        return GoogleIdentity(email=str(info["email"]).lower(), name=info.get("name"))
