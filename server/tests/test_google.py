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


async def test_plusieurs_adresses_par_personne(mohamed, kevin):
    """Chacun peut avoir son adresse pro et sa perso : les deux ouvrent HQ."""
    r = await mohamed.post("/api/members/kevin/emails", json={"email": "  Kevin@Nyuman.App "})
    assert r.status_code == 200 and r.json()["emails"] == ["kevin@nyuman.app"]
    r = await mohamed.post("/api/members/kevin/emails", json={"email": "kevin.perso@gmail.com"})
    assert r.json()["emails"] == ["kevin.perso@gmail.com", "kevin@nyuman.app"]
    # une adresse n'appartient qu'à une personne
    assert (await mohamed.post("/api/members/carmel/emails", json={"email": "kevin@nyuman.app"})).status_code == 400
    assert (await mohamed.post("/api/members/kevin/emails", json={"email": "pasuneadresse"})).status_code == 400
    # on peut en retirer une
    assert (await mohamed.delete("/api/members/kevin/emails/kevin.perso@gmail.com")).json()["emails"] == ["kevin@nyuman.app"]


async def test_retour_de_google_reconnait_l_adresse(mohamed, google, monkeypatch):
    await mohamed.post("/api/members/carmel/emails", json={"email": "carmel@nyuman.app"})
    await mohamed.post("/api/members/carmel/emails", json={"email": "carmel.perso@gmail.com"})

    async def fake(code):
        return {"bon": "carmel@nyuman.app", "perso": "Carmel.Perso@Gmail.com",
                "inconnu": "quelqu-un@ailleurs.com"}[code]
    monkeypatch.setattr(auth, "google_email", fake)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        start = await c.get("/api/auth/google/start", follow_redirects=False)
        assert start.status_code == 302 and "accounts.google.com" in start.headers["location"]
        state = start.headers["location"].split("state=")[1].split("&")[0]
        r = await c.get(f"/api/auth/google/callback?state={state}&code=bon", follow_redirects=False)
        assert r.status_code == 302 and r.headers["location"] == "/accueil"
        assert (await c.get("/api/auth/me")).json()["id"] == "carmel"

    # sa deuxième adresse ouvre la même fiche
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        start = await c.get("/api/auth/google/start", follow_redirects=False)
        state = start.headers["location"].split("state=")[1].split("&")[0]
        await c.get(f"/api/auth/google/callback?state={state}&code=perso", follow_redirects=False)
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


async def test_adresse_de_secours_pour_la_premiere_connexion(client, google, monkeypatch):
    """Avant que les fiches soient remplies, une adresse posée par Kevin laisse entrer le DG."""
    monkeypatch.setattr(settings, "bootstrap_emails", "patron@exemple.com=mohamed")

    async def fake(code):
        return "Patron@Exemple.com"
    monkeypatch.setattr(auth, "google_email", fake)
    start = await client.get("/api/auth/google/start", follow_redirects=False)
    state = start.headers["location"].split("state=")[1].split("&")[0]
    r = await client.get(f"/api/auth/google/callback?state={state}&code=x", follow_redirects=False)
    assert r.headers["location"] == "/accueil"
    assert (await client.get("/api/auth/me")).json()["id"] == "mohamed"
