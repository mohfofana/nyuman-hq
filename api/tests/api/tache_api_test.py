from datetime import date, timedelta

from core.realtime.broker import broker
from tests.conftest import login


async def _agent_id(client, name="Prospection"):
    return next(m["id"] for m in (await client.get("/api/membres")).json() if m["name"] == name)


async def test_creer_une_tache_pour_un_agent_et_la_voir_au_tableau(client):
    me = await login(client)
    prospection = await _agent_id(client)
    response = await client.post(
        "/api/taches",
        json={"title": "Qualifier 30 barbiers à Cocody", "assignee_id": prospection, "due_date": str(date.today() + timedelta(days=5))},
    )
    assert response.status_code == 201
    tache = response.json()
    assert tache["status"] == "a_faire" and tache["assignee"]["name"] == "Prospection"
    assert tache["created_by"]["id"] == me["id"]

    board = (await client.get("/api/taches")).json()
    assert [t["title"] for t in board] == ["Qualifier 30 barbiers à Cocody"]
    feed = (await client.get("/api/evenements")).json()
    assert feed[0]["text"] == "a créé la tâche « Qualifier 30 barbiers à Cocody » et l’a confiée à Prospection."


async def test_la_tache_sert_l_objectif_du_trimestre(client):
    await login(client)
    today = date.today()
    objectif = (await client.put("/api/objectifs/courant", json={
        "title": "100 pros actifs", "quarter": "T4", "metric": "pros_actifs", "target": 100,
        "start_date": str(today - timedelta(days=5)), "end_date": str(today + timedelta(days=60)),
    })).json()
    liee = (await client.post("/api/taches", json={"title": "Appeler 10 salons"})).json()
    libre = (await client.post("/api/taches", json={"title": "Ranger le drive", "objectif": False})).json()
    assert liee["objectif_id"] == objectif["id"] and libre["objectif_id"] is None


async def test_deplacer_terminer_et_retirer_la_personne(client):
    await login(client)
    tache = (await client.post("/api/taches", json={"title": "Corriger le paiement"})).json()

    moved = (await client.patch(f"/api/taches/{tache['id']}", json={"status": "en_cours", "position": 0.5})).json()
    assert moved["status"] == "en_cours" and moved["position"] == 0.5

    done = (await client.patch(f"/api/taches/{tache['id']}", json={"status": "fait"})).json()
    assert done["done_at"] is not None
    assert (await client.get("/api/evenements")).json()[0]["text"] == "a terminé la tâche « Corriger le paiement »."

    reopened = (await client.patch(f"/api/taches/{tache['id']}", json={"status": "a_faire"})).json()
    assert reopened["done_at"] is None

    kevin = (await client.post("/api/membres", json={"email": "kevin@example.com", "name": "Kevin", "role": "membre"})).json()
    given = (await client.patch(f"/api/taches/{tache['id']}", json={"assignee_id": kevin["id"]})).json()
    assert given["assignee"]["name"] == "Kevin"
    assert (await client.get("/api/evenements")).json()[0]["text"] == "a confié la tâche « Corriger le paiement » à Kevin."
    # Envoyer un champ à null le vide ; ne pas l'envoyer ne change rien.
    untouched = (await client.patch(f"/api/taches/{tache['id']}", json={"title": "Corriger le paiement Wave"})).json()
    assert untouched["assignee"]["name"] == "Kevin"
    cleared = (await client.patch(f"/api/taches/{tache['id']}", json={"assignee_id": None})).json()
    assert cleared["assignee"] is None


async def test_le_tableau_se_met_a_jour_en_direct(client):
    await login(client)
    tache = (await client.post("/api/taches", json={"title": "Préparer la démo"})).json()
    queue = broker.subscribe()
    try:
        await client.patch(f"/api/taches/{tache['id']}", json={"status": "en_attente"})
        messages = [queue.get_nowait() for _ in range(queue.qsize())]
    finally:
        broker.unsubscribe(queue)
    assert {"type": "changement", "sujets": ["taches"]} in messages


async def test_la_corbeille_retire_la_tache_du_tableau(client):
    await login(client)
    tache = (await client.post("/api/taches", json={"title": "Doublon"})).json()
    assert (await client.post(f"/api/taches/{tache['id']}/archiver")).status_code == 200
    assert (await client.get("/api/taches")).json() == []
    assert [t["title"] for t in (await client.get("/api/taches", params={"archives": "true"})).json()] == ["Doublon"]


async def test_on_ne_confie_pas_une_tache_a_un_inconnu(client):
    await login(client)
    assert (await client.post("/api/taches", json={"title": "X", "assignee_id": 999})).status_code == 400
    assert (await client.post("/api/taches", json={"title": "X", "status": "poubelle"})).status_code == 422
