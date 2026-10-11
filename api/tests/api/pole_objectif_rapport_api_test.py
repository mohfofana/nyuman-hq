from datetime import date, timedelta

from tests.conftest import login


def _objectif(**overrides):
    today = date.today()
    body = {
        "title": "0 bug bloquant avant le lancement",
        "quarter": "T4 2026",
        "metric": "manuel",
        "target": 20,
        "current_manual": 5,
        "start_date": str(today - timedelta(days=10)),
        "end_date": str(today + timedelta(days=70)),
    }
    body.update(overrides)
    return body


async def test_un_pole_a_son_objectif_suivi_a_la_main(client):
    await login(client)
    response = await client.put("/api/objectifs/courant", params={"pole": "produit"}, json=_objectif(title="20 bugs corrigés"))
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["pole"] == "produit" and data["current"] == 5 and data["progress"] == 0.25

    # L'objectif de la maison reste à part.
    assert (await client.get("/api/objectifs/courant")).json() is None
    poles = (await client.get("/api/objectifs/poles")).json()
    assert list(poles) == ["produit"] and poles["produit"]["title"] == "20 bugs corrigés"

    feed = (await client.get("/api/evenements")).json()
    assert feed[0]["text"] == "a fixé l’objectif du pôle Produit : « 20 bugs corrigés »."


async def test_le_pole_met_a_jour_son_chiffre(client):
    await login(client)
    objectif = (await client.put("/api/objectifs/courant", params={"pole": "croissance"}, json=_objectif(title="1 000 abonnés TikTok", target=1000, current_manual=120))).json()

    # Un membre du pôle Croissance peut avancer le chiffre ; un membre d'un autre pôle, non.
    await client.post("/api/membres", json={"email": "awa@example.com", "name": "Awa", "role": "membre", "pole": "croissance"})
    await client.post("/api/membres", json={"email": "yao@example.com", "name": "Yao", "role": "membre", "pole": "produit"})
    await login(client, "awa@example.com")
    updated = await client.patch(f"/api/objectifs/{objectif['id']}/avancement", json={"value": 340})
    assert updated.status_code == 200 and updated.json()["current"] == 340
    await login(client, "yao@example.com")
    assert (await client.patch(f"/api/objectifs/{objectif['id']}/avancement", json={"value": 999})).status_code == 403


async def test_un_chiffre_de_l_app_ne_se_modifie_pas_a_la_main(client):
    await login(client)
    objectif = (await client.put("/api/objectifs/courant", params={"pole": "operations"}, json=_objectif(title="50 pros", metric="pros_actifs", target=50))).json()
    assert objectif["current"] == 38  # chiffre en direct de l'app (doublure des tests)
    assert (await client.patch(f"/api/objectifs/{objectif['id']}/avancement", json={"value": 40})).status_code == 400


async def test_publier_puis_completer_son_rapport_de_la_semaine(client):
    me = await login(client)
    body = {"fait": "Contrat FeexPay relu", "en_cours": "Négo des frais d’envoi", "bloque": "", "propositions": "Tester 50 FCFA sur 20 barbiers\nAppeler 10 salons à Angré"}
    first = await client.put("/api/rapports/moi", json=body)
    assert first.status_code == 200
    again = await client.put("/api/rapports/moi", json={**body, "bloque": "En attente de la doc FeexPay"})
    assert again.json()["id"] == first.json()["id"] and again.json()["bloque"] == "En attente de la doc FeexPay"

    mine = (await client.get("/api/rapports", params={"auteur": me["id"]})).json()
    assert len(mine) == 1
    semaine = (await client.get("/api/rapports/semaine")).json()
    assert [r["author_id"] for r in semaine["rapports"]] == [me["id"]]

    feed = [e["text"] for e in (await client.get("/api/evenements")).json()]
    assert sum(t.startswith("a publié son rapport de la semaine") for t in feed) == 1  # une seule annonce par semaine


async def test_un_rapport_vide_ou_avec_trop_de_propositions_est_refuse(client):
    await login(client)
    assert (await client.put("/api/rapports/moi", json={})).status_code == 400
    trop = {"fait": "x", "propositions": "a\nb\nc\nd"}
    assert (await client.put("/api/rapports/moi", json=trop)).status_code == 400
