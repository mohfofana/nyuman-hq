from tests.conftest import login


async def test_priorite_et_sous_etapes_d_une_tache(client):
    me = await login(client)
    tache = (await client.post("/api/taches", json={"title": "Workshop de lancement", "priority": "P1"})).json()
    assert tache["priority"] == "P1" and tache["etapes"] == []

    response = await client.post(
        f"/api/taches/{tache['id']}/etapes",
        json={"title": "Réserver le lieu", "responsable_id": me["id"], "livrable": "Lieu confirmé", "due_date": "2026-10-20"},
    )
    assert response.status_code == 201
    etape = response.json()["etapes"][0]
    assert etape["title"] == "Réserver le lieu" and etape["responsable"]["id"] == me["id"] and etape["status"] == "a_faire"

    await client.post(f"/api/taches/{tache['id']}/etapes", json={"title": "Inviter les pros"})
    done = await client.patch(f"/api/taches/{tache['id']}/etapes/{etape['id']}", json={"status": "fait"})
    assert [e["status"] for e in done.json()["etapes"]] == ["fait", "a_faire"]

    removed = await client.post(f"/api/taches/{tache['id']}/etapes/{etape['id']}/archiver")
    assert [e["title"] for e in removed.json()["etapes"]] == ["Inviter les pros"]

    listed = (await client.get("/api/taches")).json()
    assert listed[0]["etapes"][0]["title"] == "Inviter les pros"

    changed = await client.patch(f"/api/taches/{tache['id']}", json={"priority": ""})
    assert changed.json()["priority"] == ""


async def test_une_priorite_inconnue_ou_une_etape_d_une_autre_tache_est_refusee(client):
    await login(client)
    assert (await client.post("/api/taches", json={"title": "X", "priority": "P9"})).status_code == 422
    a = (await client.post("/api/taches", json={"title": "A"})).json()
    b = (await client.post("/api/taches", json={"title": "B"})).json()
    etape = (await client.post(f"/api/taches/{a['id']}/etapes", json={"title": "A.1"})).json()["etapes"][0]
    response = await client.patch(f"/api/taches/{b['id']}/etapes/{etape['id']}", json={"status": "fait"})
    assert response.status_code == 400
