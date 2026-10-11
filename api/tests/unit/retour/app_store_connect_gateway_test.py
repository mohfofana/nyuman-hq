import httpx
import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

from adapters.common.ports.out.app_store_connect_gateway import AppStoreConnectGateway

# Réponse d'exemple au format de l'API App Store Connect (JSON:API).
SCREENSHOTS = {
    "data": [
        {
            "type": "betaFeedbackScreenshotSubmissions",
            "id": "shot-1",
            "attributes": {
                "createdDate": "2026-10-09T08:15:00Z",
                "comment": "Le prix ne s’affiche pas",
                "email": "testeur@example.com",
                "deviceModel": "iPhone15,2",
                "osVersion": "18.0.1",
                "locale": "fr-CI",
                "screenshots": [{"url": "https://apple.example/a.png", "width": 1179, "height": 2556, "expirationDate": "2026-10-10T08:15:00Z"}],
            },
            "relationships": {"build": {"data": {"type": "builds", "id": "b-14"}}},
        }
    ],
    "included": [{"type": "builds", "id": "b-14", "attributes": {"version": "14"}}],
}
CRASHES = {
    "data": [
        {
            "type": "betaFeedbackCrashSubmissions",
            "id": "crash-1",
            "attributes": {"createdDate": "2026-10-09T09:00:00Z", "comment": None, "deviceModel": "iPhone13,1", "osVersion": "17.6"},
            "relationships": {"build": {"data": None}},
        }
    ]
}


def _key_pair():
    key = ec.generate_private_key(ec.SECP256R1())
    pem = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
    return pem.decode(), key.public_key()


async def test_lit_captures_et_plantages_avec_un_jeton_signe():
    private_pem, public_key = _key_pair()
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if request.url.path.endswith("betaFeedbackScreenshotSubmissions"):
            return httpx.Response(200, json=SCREENSHOTS)
        return httpx.Response(200, json=CRASHES)

    gateway = AppStoreConnectGateway("issuer-1", "KEY123", private_pem, "6470000000", transport=httpx.MockTransport(handler))
    assert gateway.configured
    retours = await gateway.fetch()

    capture, crash = retours
    assert capture.kind == "capture" and capture.comment == "Le prix ne s’affiche pas"
    assert capture.build_version == "14" and capture.screenshot_urls == ["https://apple.example/a.png"]
    assert capture.created_at.isoformat() == "2026-10-09T08:15:00+00:00"
    assert crash.kind == "plantage" and crash.comment == "" and crash.build_version == ""

    assert seen[0].url.path == "/v1/apps/6470000000/betaFeedbackScreenshotSubmissions"
    assert seen[0].url.params["sort"] == "-createdDate"
    token = seen[0].headers["Authorization"].removeprefix("Bearer ")
    assert jwt.get_unverified_header(token)["kid"] == "KEY123"
    claims = jwt.decode(token, public_key, algorithms=["ES256"], audience="appstoreconnect-v1")
    assert claims["iss"] == "issuer-1" and claims["exp"] - claims["iat"] <= 1200


def test_sans_cle_rien_n_est_appele():
    assert AppStoreConnectGateway(None, None, None, None).configured is False
