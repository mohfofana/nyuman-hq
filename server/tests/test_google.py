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
        return {"bon": ("carmel@nyuman.app", "Carmel Didi"),
                "perso": ("carmel.perso@gmail.com", "Carmel Didi"),
                "inconnu": ("quelqu-un@ailleurs.com", "Quelqu'un")}[code]
    monkeypatch.setattr(auth, "google_identity", fake)

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
        # adresse inconnue : on l'envoie se présenter, mais elle n'est pas connectée
        assert r.headers["location"] == "/rejoindre"
        assert (await c.get("/api/auth/me")).status_code == 401


async def test_state_bidon_refuse(client, google):
    r = await client.get("/api/auth/google/callback?state=invente&code=bon", follow_redirects=False)
    assert "erreur=" in r.headers["location"]


async def test_adresse_de_secours_pour_la_premiere_connexion(client, google, monkeypatch):
    """Avant que les fiches soient remplies, une adresse posée par Kevin laisse entrer le DG."""
    monkeypatch.setattr(settings, "bootstrap_emails", "patron@exemple.com=mohamed")

    async def fake(code):
        return ("patron@exemple.com", "Le patron")
    monkeypatch.setattr(auth, "google_identity", fake)
    start = await client.get("/api/auth/google/start", follow_redirects=False)
    state = start.headers["location"].split("state=")[1].split("&")[0]
    r = await client.get(f"/api/auth/google/callback?state={state}&code=x", follow_redirects=False)
    assert r.headers["location"] == "/accueil"
    assert (await client.get("/api/auth/me")).json()["id"] == "mohamed"


async def test_invitation_range_l_adresse_toute_seule(mohamed, google, monkeypatch):
    """Un responsable envoie un lien ; la personne se connecte avec Google et son adresse se range."""
    r = await mohamed.post("/api/auth/invites/yannis")
    assert r.status_code == 200
    token = r.json()["url"].rsplit("/", 1)[1]

    async def fake(code):
        return ("yannis.sika@gmail.com", "Yannis Sika")
    monkeypatch.setattr(auth, "google_identity", fake)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        start = await c.get(f"/api/auth/invite/{token}", follow_redirects=False)
        assert start.status_code == 302 and "accounts.google.com" in start.headers["location"]
        state = start.headers["location"].split("state=")[1].split("&")[0]
        back = await c.get(f"/api/auth/google/callback?state={state}&code=x", follow_redirects=False)
        assert back.headers["location"] == "/accueil"
        assert (await c.get("/api/auth/me")).json()["id"] == "yannis"

    # l'adresse est bien sur sa fiche, et le lien ne resert pas
    membres = {m["id"]: m for m in (await mohamed.get("/api/members")).json()}
    assert membres["yannis"]["emails"] == ["yannis.sika@gmail.com"]
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        assert "erreur=" in (await c.get(f"/api/auth/invite/{token}", follow_redirects=False)).headers["location"]


async def test_seul_un_responsable_invite(kevin, google):
    from tests.conftest import login_as
    autre = await login_as("yannis")
    assert (await autre.post("/api/auth/invites/fatym")).status_code == 403
    await autre.aclose()
    assert (await kevin.post("/api/auth/invites/fatym")).status_code == 200


async def test_il_se_presente_un_responsable_confirme(mohamed, google, monkeypatch):
    """Quelqu'un arrive avec une adresse inconnue : il dit qui il est, un responsable confirme."""
    await mohamed.post("/api/members/mohamed/emails", json={"email": "mohamed.fofana@nyuman.app"})

    async def fake(code):
        return ("fatym.ako@gmail.com", "Fatym Ako")
    monkeypatch.setattr(auth, "google_identity", fake)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as elle:
        start = await elle.get("/api/auth/google/start", follow_redirects=False)
        state = start.headers["location"].split("state=")[1].split("&")[0]
        r = await elle.get(f"/api/auth/google/callback?state={state}&code=x", follow_redirects=False)
        assert r.headers["location"] == "/rejoindre"

        # on lui propose les fiches encore libres, jamais celles déjà prises
        me = (await elle.get("/api/auth/join/me")).json()
        assert me["email"] == "fatym.ako@gmail.com" and me["name_seen"] == "Fatym Ako"
        libres = {c["id"] for c in me["candidates"]}
        assert "fatym" in libres and "mohamed" not in libres

        assert (await elle.post("/api/auth/join", json={"member_id": "fatym"})).json()["waiting"] == "fatym"
        assert (await elle.get("/api/auth/me")).status_code == 401  # pas encore entrée

        # le responsable voit la demande et dit oui
        demandes = (await mohamed.get("/api/members/join-requests")).json()
        assert [d["email"] for d in demandes] == ["fatym.ako@gmail.com"]
        assert demandes[0]["member_name"] == "Fatym Ako"
        assert (await mohamed.post("/api/members/join-requests/fatym.ako@gmail.com/oui")).json()["emails"] \
            == ["fatym.ako@gmail.com"]

        # maintenant elle entre
        start = await elle.get("/api/auth/google/start", follow_redirects=False)
        state = start.headers["location"].split("state=")[1].split("&")[0]
        r = await elle.get(f"/api/auth/google/callback?state={state}&code=x", follow_redirects=False)
        assert r.headers["location"] == "/accueil"
        assert (await elle.get("/api/auth/me")).json()["id"] == "fatym"


async def test_un_non_responsable_ne_confirme_personne(mohamed, google, monkeypatch):
    from tests.conftest import login_as

    async def fake(code):
        return ("maxime.e@gmail.com", "Maxime")
    monkeypatch.setattr(auth, "google_identity", fake)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as lui:
        start = await lui.get("/api/auth/google/start", follow_redirects=False)
        state = start.headers["location"].split("state=")[1].split("&")[0]
        await lui.get(f"/api/auth/google/callback?state={state}&code=x", follow_redirects=False)
        await lui.post("/api/auth/join", json={"member_id": "maxime"})

    await mohamed.post("/api/members/yannis/emails", json={"email": "yannis@nyuman.app"})
    yannis = await login_as("yannis")
    assert (await yannis.get("/api/members/join-requests")).json() == []
    assert (await yannis.post("/api/members/join-requests/maxime.e@gmail.com/oui")).status_code == 403
    await yannis.aclose()
