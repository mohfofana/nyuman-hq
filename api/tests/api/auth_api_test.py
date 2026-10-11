from tests.conftest import HEAD_EMAIL, login


async def test_une_route_protegee_demande_une_session(client):
    response = await client.get("/api/membres")
    assert response.status_code == 401
    assert "Connecte-toi" in response.json()["detail"]


async def test_la_config_de_connexion_est_publique(client):
    response = await client.get("/api/auth/config")
    assert response.status_code == 200
    assert response.json() == {
        "google_client_id": "client-test.apps.googleusercontent.com",
        "dev_login": True,
        "email_login": True,
    }


async def test_connexion_dev_puis_me_puis_sortie(client):
    me = await login(client)
    assert me["email"] == HEAD_EMAIL and me["role"] == "head" and me["status"] == "en_ligne"

    response = await client.get("/api/auth/me")
    assert response.status_code == 200

    await client.post("/api/auth/logout")
    assert (await client.get("/api/auth/me")).status_code == 401


async def test_une_adresse_inconnue_est_refusee(client):
    response = await client.post("/api/auth/dev", json={"email": "inconnu@exemple.com"})
    assert response.status_code == 403


async def test_un_agent_ne_peut_pas_se_connecter(client):
    # Les agents n'ont pas d'adresse : aucune session ne peut être ouverte à leur nom.
    await login(client)
    agents = [m for m in (await client.get("/api/membres")).json() if m["kind"] == "agent"]
    assert len(agents) == 3 and all(a["email"] is None for a in agents)


async def test_connexion_google_remplace_le_nom_provisoire(client):
    response = await client.post("/api/auth/google", json={"credential": f"ok:{HEAD_EMAIL}:Awa Diallo"})
    assert response.status_code == 200
    assert response.json()["name"] == "Awa Diallo"
    assert response.json()["initials"] == "AD"

    feed = (await client.get("/api/evenements")).json()
    assert feed[0]["text"] == "est entré dans la maison pour la première fois."


async def test_connexion_google_refusee_pour_un_jeton_faux_ou_une_adresse_inconnue(client):
    assert (await client.post("/api/auth/google", json={"credential": "faux-jeton-123"})).status_code == 401
    unknown = await client.post("/api/auth/google", json={"credential": "ok:x@exemple.com:X"})
    assert unknown.status_code == 403


async def test_une_ecriture_venue_d_un_autre_site_est_refusee(client):
    response = await client.post(
        "/api/auth/dev", json={"email": HEAD_EMAIL}, headers={"Origin": "https://site-malveillant.example"}
    )
    assert response.status_code == 403
