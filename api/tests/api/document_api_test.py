from tests.conftest import login


async def _create(client, title="Contrat type des pros", content="# Article 1"):
    response = await client.post("/api/documents", json={"title": title, "category": "contrats", "content": content})
    assert response.status_code == 201, response.text
    return response.json()


async def test_le_cerveau_commun_est_depose_au_demarrage(client):
    await login(client)
    docs = (await client.get("/api/documents", params={"categorie": "cerveau"})).json()
    assert [d["title"] for d in docs] == ["Objectifs Nyuman"]
    full = (await client.get(f"/api/documents/{docs[0]['id']}")).json()
    assert "580 pros actifs" in full["content"]
    # L'extrait se lit sans la mise en forme Markdown.
    assert docs[0]["excerpt"].startswith("Ce document est le cerveau commun")
    assert "#" not in docs[0]["excerpt"] and "**" not in docs[0]["excerpt"]


async def test_creer_modifier_et_garder_chaque_version(client):
    await login(client)
    doc = await _create(client)
    assert doc["version"] == 1

    updated = await client.put(
        f"/api/documents/{doc['id']}",
        json={"title": doc["title"], "category": "contrats", "content": "# Article 1\nModifié", "base_version": 1},
    )
    assert updated.status_code == 200 and updated.json()["version"] == 2

    versions = (await client.get(f"/api/documents/{doc['id']}/versions")).json()
    assert [v["version"] for v in versions] == [2, 1]
    first = (await client.get(f"/api/documents/{doc['id']}/versions/1")).json()
    assert first["content"] == "# Article 1"

    feed = [e["text"] for e in (await client.get("/api/evenements")).json()]
    assert feed[0] == "a modifié le document « Contrat type des pros » (version 2)."
    assert feed[1] == "a créé le document « Contrat type des pros »."


async def test_une_modification_sur_une_version_perimee_est_refusee(client):
    await login(client)
    doc = await _create(client)
    body = {"title": doc["title"], "category": "contrats", "content": "v2", "base_version": 1}
    assert (await client.put(f"/api/documents/{doc['id']}", json=body)).status_code == 200
    stale = await client.put(f"/api/documents/{doc['id']}", json={**body, "content": "autre v2"})
    assert stale.status_code == 409


async def test_la_corbeille_ne_supprime_rien(client):
    await login(client)
    doc = await _create(client)
    assert (await client.post(f"/api/documents/{doc['id']}/archiver")).json()["archived"] is True

    titles = [d["title"] for d in (await client.get("/api/documents")).json()]
    assert "Contrat type des pros" not in titles
    in_trash = (await client.get("/api/documents", params={"archives": "true"})).json()
    assert [d["title"] for d in in_trash] == ["Contrat type des pros"]

    blocked = await client.put(
        f"/api/documents/{doc['id']}",
        json={"title": "x", "category": "contrats", "content": "", "base_version": 1},
    )
    assert blocked.status_code == 400
    assert (await client.post(f"/api/documents/{doc['id']}/restaurer")).json()["archived"] is False


async def test_la_recherche_lit_le_titre_et_le_contenu(client):
    await login(client)
    await _create(client, "Compte rendu du 7 octobre", "Décision : grille à 2 %, minimum 100 FCFA")
    await _create(client, "Pitch", "Nyuman en 10 diapositives")
    found = (await client.get("/api/documents", params={"q": "décision : grille"})).json()
    assert [d["title"] for d in found] == ["Compte rendu du 7 octobre"]
    assert len((await client.get("/api/documents", params={"q": "100%"})).json()) == 0


async def test_un_rayon_inconnu_est_refuse(client):
    await login(client)
    response = await client.post("/api/documents", json={"title": "X", "category": "inconnu", "content": ""})
    assert response.status_code == 422
