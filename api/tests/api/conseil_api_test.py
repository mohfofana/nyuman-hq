from datetime import datetime, timedelta, timezone

from sqlalchemy import update

from adapters.core.decision.entity.decision_entity import DecisionEntity
from tests.conftest import login


async def _membre_simple(client) -> None:
    await client.post("/api/membres", json={"email": "awa@example.com", "name": "Awa", "role": "membre", "pole": "operations"})


async def test_un_membre_propose_les_heads_votent_et_tranchent(client):
    await login(client)
    await _membre_simple(client)
    await login(client, "awa@example.com")

    response = await client.post(
        "/api/decisions",
        json={
            "titre": "Commission Wave : pro ou Nyuman ?",
            "demande": "Le retrait Wave coûte 1 % de l’acompte.",
            "pole_concerne": "operations",
            "poles_en_charge": ["operations", "direction"],
            "objectif": "Garder la marge nette par réservation",
            "risques": "Les pros pourraient refuser",
        },
    )
    assert response.status_code == 201
    sujet = response.json()
    assert sujet["statut"] == "nouveau" and sujet["poles_en_charge"] == ["operations", "direction"]

    # Un membre ne vote pas et ne tranche pas.
    assert (await client.put(f"/api/decisions/{sujet['id']}/vote", json={"vote": "pour"})).status_code == 403
    assert (await client.patch(f"/api/decisions/{sujet['id']}", json={"statut": "valide"})).status_code == 403
    # Mais il peut préciser son propre sujet.
    assert (await client.patch(f"/api/decisions/{sujet['id']}", json={"risques": "Refus possible"})).status_code == 200

    await login(client)
    voted = await client.put(f"/api/decisions/{sujet['id']}/vote", json={"vote": "contre", "commentaire": "À absorber"})
    assert voted.status_code == 200 and voted.json()["votes"][0]["vote"] == "contre"
    revote = await client.put(f"/api/decisions/{sujet['id']}/vote", json={"vote": "pour"})
    assert [v["vote"] for v in revote.json()["votes"]] == ["pour"]

    decided = await client.patch(f"/api/decisions/{sujet['id']}", json={"statut": "valide", "decision": "Nyuman absorbe la commission."})
    body = decided.json()
    assert body["statut"] == "valide" and body["decided_at"] and body["decided_by"]["name"]
    assert body["revue_le"] and body["a_revoir"] is False

    # Une fois tranché, on ne vote plus.
    assert (await client.put(f"/api/decisions/{sujet['id']}/vote", json={"vote": "contre"})).status_code == 400

    feed = [e["text"] for e in (await client.get("/api/evenements")).json()]
    assert "a tranché : oui à « Commission Wave : pro ou Nyuman ? »." in feed
    assert "a mis au conseil : « Commission Wave : pro ou Nyuman ? »." in feed


async def test_revue_a_30_jours_puis_bilan(client, session_factory):
    await login(client)
    sujet = (await client.post("/api/decisions", json={"titre": "Ticket coupe-file à 100 FCFA"})).json()
    await client.patch(f"/api/decisions/{sujet['id']}", json={"statut": "valide"})

    async with session_factory() as session:
        await session.execute(update(DecisionEntity).values(decided_at=datetime.now(timezone.utc) - timedelta(days=31)))
        await session.commit()
    listed = (await client.get("/api/decisions")).json()
    assert listed[0]["a_revoir"] is True

    bilan = await client.put(f"/api/decisions/{sujet['id']}/bilan", json={"verdict": "bonne", "bilan": "Le volume des barbers a doublé."})
    assert bilan.status_code == 200
    assert bilan.json()["a_revoir"] is False and bilan.json()["bilan_verdict"] == "bonne"


async def test_pas_de_bilan_avant_d_avoir_tranche(client):
    await login(client)
    sujet = (await client.post("/api/decisions", json={"titre": "Abonnement Pro"})).json()
    response = await client.put(f"/api/decisions/{sujet['id']}/bilan", json={"verdict": "bonne"})
    assert response.status_code == 400


async def test_retirer_un_sujet_le_garde_en_base(client):
    await login(client)
    sujet = (await client.post("/api/decisions", json={"titre": "Sujet en double"})).json()
    assert (await client.post(f"/api/decisions/{sujet['id']}/archiver")).status_code == 200
    assert (await client.get("/api/decisions")).json() == []
