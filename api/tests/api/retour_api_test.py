from datetime import datetime, timezone

from tests.conftest import login
from use_cases.common.ports.out.testflight_gateway import RetourSource

PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 64


async def _post_bug(client, comment="L’app plante quand je paie l’acompte avec Wave", files=None):
    return await client.post(
        "/api/retours",
        data={"kind": "bug", "comment": comment, "espace": "cliente", "device_model": "iPhone 13", "os_version": "18.1", "build_version": "14"},
        files=files if files is not None else [("captures", ("ecran.png", PNG, "image/png"))],
    )


async def test_signaler_un_bug_avec_capture_au_lieu_de_whatsapp(client, storage):
    me = await login(client)
    response = await _post_bug(client)
    assert response.status_code == 201, response.text
    retour = response.json()
    assert retour["kind"] == "bug" and retour["author"]["id"] == me["id"] and retour["captures"] == 1

    image = await client.get(f"/api/retours/{retour['id']}/captures/0")
    assert image.status_code == 200 and image.headers["content-type"] == "image/png" and image.content == PNG
    assert (await client.get(f"/api/retours/{retour['id']}/captures/1")).status_code == 404

    feed = (await client.get("/api/evenements")).json()
    assert feed[0]["text"] == "a signalé un bug : « L’app plante quand je paie l’acompte avec Wave »."
    assert (await client.get("/api/retours/etat")).json()["nouveaux"] == 1


async def test_un_retour_vide_ou_un_fichier_qui_n_est_pas_une_image_est_refuse(client):
    await login(client)
    assert (await _post_bug(client, comment="  ", files=[])).status_code == 400
    texte = await _post_bug(client, files=[("captures", ("notes.txt", b"bonjour", "text/plain"))])
    assert texte.status_code == 400


async def test_transformer_un_retour_en_tache(client):
    await login(client)
    retour = (await _post_bug(client)).json()
    kevin = (await client.post("/api/membres", json={"email": "kevin@example.com", "name": "Kevin", "role": "membre"})).json()

    response = await client.post(f"/api/retours/{retour['id']}/tache", json={"assignee_id": kevin["id"]})
    assert response.status_code == 201
    tache = response.json()
    assert tache["title"].startswith("Bug : L’app plante") and tache["assignee"]["name"] == "Kevin"
    assert tache["retour_id"] == retour["id"]
    assert "iPhone 13, iOS 18.1" in tache["description"] and "Build : 14" in tache["description"]

    assert (await client.get("/api/retours")).json() == []  # plus dans la boîte des nouveaux
    done = (await client.get("/api/retours", params={"statut": "en_tache"})).json()
    assert done[0]["tache_id"] == tache["id"]
    assert (await client.post(f"/api/retours/{retour['id']}/tache", json={})).status_code == 400  # pas deux fois

    feed = [e["text"] for e in (await client.get("/api/evenements")).json()]
    assert feed[0] == f"a transformé un retour en tâche : « {tache['title']} »."


async def test_classer_un_retour(client):
    await login(client)
    retour = (await _post_bug(client)).json()
    assert (await client.post(f"/api/retours/{retour['id']}/classer")).json()["statut"] == "classe"
    assert (await client.get("/api/retours")).json() == []


async def test_import_testflight_sans_doublons(client, testflight):
    await login(client)
    assert (await client.post("/api/retours/synchroniser")).status_code == 400  # pas de clé : pas d'import
    testflight.is_configured = True
    testflight.sources = [
        RetourSource(asc_id="AbC1", kind="capture", created_at=datetime(2026, 10, 9, 10, tzinfo=timezone.utc),
                     comment="Le bouton est caché", email="testeur@example.com", device_model="iPhone 15",
                     os_version="18.0", build_version="14", screenshot_urls=["https://apple.example/1.png"]),
        RetourSource(asc_id="XyZ9", kind="plantage", created_at=datetime(2026, 10, 9, 11, tzinfo=timezone.utc)),
    ]
    assert (await client.post("/api/retours/synchroniser")).json() == {"nouveaux": 2}
    assert (await client.post("/api/retours/synchroniser")).json() == {"nouveaux": 0}

    retours = (await client.get("/api/retours")).json()
    assert {r["kind"] for r in retours} == {"bug", "remarque"}  # plantage → bug, capture → remarque
    capture = next(r for r in retours if r["captures"] == 1)
    assert capture["source"] == "testflight" and capture["tester_email"] == "testeur@example.com"
    assert (await client.get(f"/api/retours/{capture['id']}/captures/0")).status_code == 200
