import pytest
from httpx import ASGITransport, AsyncClient

from app.api import auth
from app.config import settings
from app.main import app
from tests.conftest import login_as


@pytest.fixture
def google(monkeypatch):
    monkeypatch.setattr(settings, "google_client_id", "id-de-test")
    monkeypatch.setattr(settings, "google_client_secret", "secret-de-test")
    monkeypatch.setattr(settings, "public_url", "https://hq.nyuman.app")


async def test_etat_de_la_connexion(client, google):
    r = (await client.get("/api/auth/google/status")).json()
    assert r == {"google": True, "dev_login": True}


async def test_adresse_posee_par_un_responsable(mohamed, kevin):
    r = await mohamed.put("/api/members/kevin/email", json={"email": "  Kevin@Nyuman.App "})
    assert r.status_code == 200 and r.json()["email"] == "kevin@nyuman.app"
    # pas deux fois la même adresse
    assert (await mohamed.put("/api/members/carmel/email", json={"email": "kevin@nyuman.app"})).status_code == 400
    assert (await mohamed.put("/api/members/kevin/email", json={"email": "pasuneadresse"})).status_code == 400
    # un non-responsable ne touche à rien
    autre = await login_as("abraham")
    await autre.patch("/api/members/me", json={"status_message": "x"})
    assert (await kevin.put("/api/members/kevin/email", json={"email": "a@b.co"})).status_code == 200  # kevin est head
    await autre.aclose()


async def test_retour_de_google_reconnait_l_adresse(mohamed, google, monkeypatch):
    await mohamed.put("/api/members/carmel/email", json={"email": "carmel@nyuman.app"})

    async def fake(code):
        return {"bon": "carmel@nyuman.app", "inconnu": "quelqu-un@ailleurs.com"}[code]
    monkeypatch.setattr(auth, "google_email", fake)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        start = await c.get("/api/auth/google/start", follow_redirects=False)
        assert start.status_code == 302 and "accounts.google.com" in start.headers["location"]
        state = start.headers["location"].split("state=")[1].split("&")[0]
        r = await c.get(f"/api/auth/google/callback?state={state}&code=bon", follow_redirects=False)
        assert r.status_code == 302 and r.headers["location"] == "/accueil"
        assert (await c.get("/api/auth/me")).json()["id"] == "carmel"

    # une adresse hors équipe n'entre pas
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        start = await c.get("/api/auth/google/start", follow_redirects=False)
        state = start.headers["location"].split("state=")[1].split("&")[0]
        r = await c.get(f"/api/auth/google/callback?state={state}&code=inconnu", follow_redirects=False)
        assert "erreur=" in r.headers["location"]
        assert (await c.get("/api/auth/me")).status_code == 401


async def test_state_bidon_refuse(client, google):
    r = await client.get("/api/auth/google/callback?state=invente&code=bon", follow_redirects=False)
    assert "erreur=" in r.headers["location"]
