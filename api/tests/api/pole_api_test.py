from tests.conftest import login


async def test_un_head_fait_entrer_un_head_de_pole(client):
    await login(client)
    response = await client.post(
        "/api/membres",
        json={"email": "kevin@example.com", "name": "Kevin Diakité", "title": "CTO", "role": "head", "pole": "produit"},
    )
    assert response.status_code == 201
    assert response.json()["pole"] == "produit" and response.json()["role"] == "head"


async def test_chacun_regle_son_propre_pole_mais_pas_ses_droits(client):
    me = await login(client)
    mine = await client.patch(f"/api/membres/{me['id']}", json={"title": "CEO", "pole": "direction"})
    assert mine.status_code == 200 and mine.json()["title"] == "CEO" and mine.json()["pole"] == "direction"
    assert (await client.patch(f"/api/membres/{me['id']}", json={"role": "membre"})).status_code == 400


async def test_les_agents_sont_ranges_dans_un_pole(client):
    await login(client)
    membres = {m["name"]: m for m in (await client.get("/api/membres")).json()}
    assert membres["Chef de cabinet"]["pole"] == "direction"
    assert membres["Prospection"]["pole"] == "operations"
    assert membres["Contradicteur"]["pole"] == ""  # transversal : il relit tout le monde

    # Un head peut déplacer un agent d'un pôle à l'autre.
    moved = await client.patch(f"/api/membres/{membres['Prospection']['id']}", json={"pole": "croissance"})
    assert moved.status_code == 200 and moved.json()["pole"] == "croissance"
    assert (await client.patch(f"/api/membres/{membres['Prospection']['id']}", json={"title": "x"})).status_code == 400


async def test_une_tache_prend_le_pole_de_la_personne(client):
    await login(client)
    prospection = next(m for m in (await client.get("/api/membres")).json() if m["name"] == "Prospection")
    tache = (await client.post("/api/taches", json={"title": "Qualifier 30 barbiers", "assignee_id": prospection["id"]})).json()
    assert tache["pole"] == "operations"

    forced = (await client.post("/api/taches", json={"title": "Campagne TikTok", "pole": "croissance"})).json()
    assert forced["pole"] == "croissance"
    moved = (await client.patch(f"/api/taches/{forced['id']}", json={"pole": "produit"})).json()
    assert moved["pole"] == "produit"
    assert (await client.post("/api/taches", json={"title": "X", "pole": "cuisine"})).status_code == 422
