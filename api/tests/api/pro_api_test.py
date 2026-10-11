from tests.conftest import login


async def test_le_panel_demande_une_session(client):
    assert (await client.get("/api/pros")).status_code == 401


async def test_ajouter_puis_suivre_une_pro(client):
    me = await login(client)
    response = await client.post(
        "/api/pros",
        json={
            "nom": "Aya Test",
            "categorie": "fondateur",
            "enseigne": "Salon Test",
            "audience": "10K - 30K",
            "telephone": "0700000000",
            "email": "Aya@Example.com",
            "contrat": "en_attente",
            "acces_test": "a_envoyer",
        },
    )
    assert response.status_code == 201
    pro = response.json()
    assert pro["email"] == "aya@example.com" and pro["categorie"] == "fondateur"

    sent = await client.patch(f"/api/pros/{pro['id']}", json={"acces_test": "envoye", "suivi_par_id": me["id"]})
    assert sent.json()["acces_test"] == "envoye" and sent.json()["suivi_par"]["id"] == me["id"]

    # Le fil parle de l'enseigne, jamais du téléphone ni de l'email.
    feed = " ".join(e["text"] for e in (await client.get("/api/evenements")).json())
    assert "Salon Test" in feed and "0700000000" not in feed and "aya@example.com" not in feed

    assert (await client.post(f"/api/pros/{pro['id']}/archiver")).status_code == 200
    assert (await client.get("/api/pros")).json() == []


async def test_une_fiche_mal_remplie_est_refusee(client):
    await login(client)
    assert (await client.post("/api/pros", json={"nom": "X", "email": "pas-une-adresse"})).status_code == 400
    assert (await client.post("/api/pros", json={"nom": "X", "acces_test": "inconnu"})).status_code == 422
