import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import httpx
import jwt

from use_cases.common.ports.out.testflight_gateway import RetourSource, TestflightGateway

logger = logging.getLogger("hq")

BASE_URL = "https://api.appstoreconnect.apple.com"
_RESOURCES = (("capture", "betaFeedbackScreenshotSubmissions"), ("plantage", "betaFeedbackCrashSubmissions"))


class AppStoreConnectGateway(TestflightGateway):
    """Retours des testeurs TestFlight, par l'API App Store Connect.

    Utile quand des testeurs externes passeront par TestFlight. Tant que la clé n'est pas renseignée, rien n'est appelé.
    Doc : GET /v1/apps/{id}/betaFeedbackScreenshotSubmissions et /betaFeedbackCrashSubmissions.
    """

    def __init__(
        self,
        issuer_id: Optional[str],
        key_id: Optional[str],
        private_key: Optional[str],
        app_id: Optional[str],
        transport: Optional[httpx.AsyncBaseTransport] = None,
    ):
        self._issuer_id = issuer_id
        self._key_id = key_id
        self._private_key = private_key
        self._app_id = app_id
        self._transport = transport

    @property
    def configured(self) -> bool:
        return all([self._issuer_id, self._key_id, self._private_key, self._app_id])

    def _token(self) -> str:
        # Jeton signé avec la clé privée de l'équipe (ES256), valable 15 minutes, comme l'exige Apple.
        now = int(time.time())
        return jwt.encode(
            {"iss": self._issuer_id, "iat": now, "exp": now + 900, "aud": "appstoreconnect-v1"},
            self._private_key,
            algorithm="ES256",
            headers={"kid": self._key_id, "typ": "JWT"},
        )

    async def fetch(self, limit: int = 50) -> List[RetourSource]:
        headers = {"Authorization": f"Bearer {self._token()}"}
        retours: List[RetourSource] = []
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=15.0, transport=self._transport) as client:
            for kind, resource in _RESOURCES:
                response = await client.get(
                    f"/v1/apps/{self._app_id}/{resource}",
                    params={"sort": "-createdDate", "limit": limit, "include": "build", "fields[builds]": "version"},
                    headers=headers,
                )
                response.raise_for_status()
                retours.extend(self._parse(kind, response.json()))
        return retours

    @staticmethod
    def _parse(kind: str, payload: Dict) -> List[RetourSource]:
        builds = {
            item["id"]: item.get("attributes", {}).get("version", "")
            for item in payload.get("included", [])
            if item.get("type") == "builds"
        }
        result = []
        for item in payload.get("data", []):
            a = item.get("attributes", {})
            build_id = ((item.get("relationships", {}).get("build") or {}).get("data") or {}).get("id")
            result.append(
                RetourSource(
                    asc_id=item["id"],
                    kind=kind,
                    created_at=datetime.fromisoformat(a["createdDate"].replace("Z", "+00:00")),
                    comment=a.get("comment") or "",
                    email=a.get("email"),
                    device_model=a.get("deviceModel") or "",
                    os_version=a.get("osVersion") or "",
                    locale=a.get("locale") or "",
                    build_version=builds.get(build_id, ""),
                    screenshot_urls=[s["url"] for s in a.get("screenshots") or [] if s.get("url")],
                )
            )
        return result

    async def download(self, url: str) -> Tuple[bytes, str]:
        async with httpx.AsyncClient(timeout=20.0, transport=self._transport) as client:
            response = await client.get(url)
        response.raise_for_status()
        return response.content, response.headers.get("content-type", "image/jpeg")
