from tests.conftest import login


async def test_la_maison_contient_les_agents_et_le_head_initial(client):
    await login(client)
    membres = (await client.get("/api/membres")).json()
    assert [m["name"] for m in membres if m["kind"] == "agent"] == ["Chef de cabinet", "Contradicteur", "Prospection"]
    assert membres[0]["role"] == "head"  # les heads en tête de liste
    agent = next(m for m in membres if m["kind"] == "agent")
    assert agent["status_label"] == "En préparation"


async def test_un_head_fait_entrer_quelqu_un(client):
    await login(client)
    response = await client.post(
        "/api/membres",
        json={"email": "Kevin@Example.com", "name": "Kevin", "title": "CTO", "role": "membre"},
    )
    assert response.status_code == 201
    assert response.json()["email"] == "kevin@example.com"

    duplicate = await client.post("/api/membres", json={"email": "kevin@example.com", "name": "K", "role": "membre"})
    assert duplicate.status_code == 409

    feed = (await client.get("/api/evenements")).json()
    assert feed[0]["text"] == "a fait entrer Kevin dans la maison."


async def test_un_membre_ne_peut_pas_faire_entrer_quelqu_un(client):
    await login(client)
    await client.post("/api/membres", json={"email": "kevin@example.com", "name": "Kevin", "role": "membre"})
    await login(client, "kevin@example.com")
    response = await client.post("/api/membres", json={"email": "z@example.com", "name": "Z", "role": "membre"})
    assert response.status_code == 403


async def test_retirer_l_acces_coupe_la_session(client):
    await login(client)
    kevin = (
        await client.post("/api/membres", json={"email": "kevin@example.com", "name": "Kevin", "role": "head"})
    ).json()
    response = await client.patch(f"/api/membres/{kevin['id']}", json={"active": False})
    assert response.status_code == 200 and response.json()["active"] is False
    assert (await client.post("/api/auth/dev", json={"email": "kevin@example.com"})).status_code == 403


async def test_on_ne_change_pas_ses_propres_droits(client):
    me = await login(client)
    response = await client.patch(f"/api/membres/{me['id']}", json={"role": "membre"})
    assert response.status_code == 400
