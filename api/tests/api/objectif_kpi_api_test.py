from datetime import date, timedelta

from domain.value_objects.kpi import KpiSnapshot
from tests.conftest import login


def _objectif(**overrides):
    today = date.today()
    body = {
        "title": "100 pros actifs au 31 décembre",
        "quarter": "T4 2026",
        "metric": "pros_actifs",
        "target": 100,
        "start_date": (today - timedelta(days=10)).isoformat(),
        "end_date": (today + timedelta(days=70)).isoformat(),
    }
    body.update(overrides)
    return body


async def test_pas_d_objectif_au_depart(client):
    await login(client)
    response = await client.get("/api/objectifs/courant")
    assert response.status_code == 200 and response.json() is None


async def test_un_head_fixe_l_objectif_et_la_jauge_suit_le_chiffre_en_direct(client):
    await login(client)
    response = await client.put("/api/objectifs/courant", json=_objectif())
    assert response.status_code == 200
    data = response.json()
    assert data["current"] == 38 and data["progress"] == 0.38
    assert data["weeks_left"] == 10
    assert data["needed_per_week"] == 6.2  # 62 à trouver en 10 semaines

    # Corriger l'objectif en cours ne crée pas un second objectif.
    await client.put("/api/objectifs/courant", json=_objectif(target=120))
    assert (await client.get("/api/objectifs/courant")).json()["target"] == 120


async def test_un_membre_ne_peut_pas_fixer_l_objectif(client):
    await login(client)
    await client.post("/api/membres", json={"email": "kevin@example.com", "name": "Kevin", "role": "membre"})
    await login(client, "kevin@example.com")
    assert (await client.put("/api/objectifs/courant", json=_objectif())).status_code == 403


async def test_un_chiffre_non_suivi_est_refuse(client):
    await login(client)
    assert (await client.put("/api/objectifs/courant", json=_objectif(metric="avis"))).status_code == 400


async def test_kpi_en_direct(client):
    await login(client)
    data = (await client.get("/api/kpis")).json()
    assert data["available"] is True
    assert {k["key"]: k["value"] for k in data["values"]}["revenu_nyuman_7j_fcfa"] == 23900


async def test_kpi_indisponibles_sans_casser_l_objectif(client, stats):
    await login(client)
    await client.put("/api/objectifs/courant", json=_objectif())
    stats.next = KpiSnapshot.unavailable("L’API Nyuman ne répond pas.")
    kpis = (await client.get("/api/kpis")).json()
    assert kpis == {"available": False, "reason": "L’API Nyuman ne répond pas.", "updated_at": None, "values": []}
    objectif = (await client.get("/api/objectifs/courant")).json()
    assert objectif["current"] is None and objectif["weeks_left"] == 10
