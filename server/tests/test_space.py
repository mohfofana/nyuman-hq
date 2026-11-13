from httpx import ASGITransport, AsyncClient

from app.main import app
from tests.conftest import login_as


def agent(mid):
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test", headers={"X-HQ-Agent": mid})


async def test_espace_suit_le_poste(mohamed, kevin):
    s = (await mohamed.get("/api/space")).json()
    assert s["roles"] == ["dg"] and "koffi" in s["agents"] and "departments" in s and "spend_pending" in s
    k = (await kevin.get("/api/space")).json()
    assert k["roles"] == ["tech"] and set(k["agents"]) == {"kodjo", "kwame"} and "tech" in k["dept"]
    a = await login_as("abraham")
    g = (await a.get("/api/space")).json()
    await a.aclose()
    assert g["roles"] == ["growth"] and g["agents"] == ["aminata"] and g["salons"]["à contacter"] == 0


async def test_salons_et_depenses(mohamed, kevin):
    r = await kevin.post("/api/tracks", json={"kind": "salon", "title": "Salon Awa, Cocody", "contact": "via Instagram"})
    assert r.status_code == 201 and r.json()["stage"] == "à contacter"
    assert (await kevin.patch(f"/api/tracks/{r.json()['id']}", json={"stage": "inscrit"})).json()["stage"] == "inscrit"
    assert (await kevin.patch(f"/api/tracks/{r.json()['id']}", json={"stage": "n'importe"})).status_code == 400
    d = (await kevin.post("/api/tracks", json={"kind": "depense", "title": "Railway", "amount": 15, "currency": "USD"})).json()
    async with agent("adjoua") as a:
        assert (await a.patch(f"/api/tracks/{d['id']}", json={"stage": "validée"})).status_code == 403
    ok = (await mohamed.patch(f"/api/tracks/{d['id']}", json={"stage": "validée"})).json()
    assert ok["stage"] == "validée" and ok["decided_by"] == "mohamed"


async def test_conseil_vote_et_avis(mohamed, kevin):
    p = (await kevin.post("/api/proposals", json={"title": "Payer Railway 15 $/mois", "figures": "15 $ / mois"})).json()
    assert p["status"] == "open" and len(p["voters"]) == 6
    todo = (await mohamed.get("/api/space")).json()["to_vote"]
    assert [x["id"] for x in todo] == [p["id"]]
    async with agent("adjoua") as a:
        assert (await a.post(f"/api/proposals/{p['id']}/vote", json={"choice": "pour"})).status_code == 403
        assert (await a.put(f"/api/proposals/{p['id']}/opinion", json={"opinion": "x"})).status_code == 403
    async with agent("koffi") as k:
        assert (await k.put(f"/api/proposals/{p['id']}/opinion", json={"opinion": "Oui, mais plafonner."})).json()["opinion"]
    await mohamed.post(f"/api/proposals/{p['id']}/vote", json={"choice": "pour"})
    await kevin.post(f"/api/proposals/{p['id']}/vote", json={"choice": "contre"})
    assert (await mohamed.get("/api/space")).json()["to_vote"] == []
    done = (await mohamed.post(f"/api/proposals/{p['id']}/close")).json()
    assert done["status"] == "rejected" and done["tally"] == {"pour": 1, "contre": 1, "abstention": 0}


async def test_vote_clos_quand_tous_ont_vote(mohamed):
    p = (await mohamed.post("/api/proposals", json={"title": "Brunch des pros le 12/12", "ask_critic": False})).json()
    last = None
    for h in ["mohamed", "marie-sophie", "abraham", "sullyvan", "carmel", "kevin"]:
        c = await login_as(h)
        last = (await c.post(f"/api/proposals/{p['id']}/vote", json={"choice": "pour"})).json()
        await c.aclose()
    assert last["status"] == "adopted"


async def test_departements_disent_a_qui_s_adresser(mohamed):
    """Le DG voit, pour chaque département, qui le dirige et ce qui traîne."""
    p = (await mohamed.post("/api/projects", json={"name": "Lancement", "department": "Croissance"})).json()
    await mohamed.post("/api/tasks", json={"project_id": p["id"], "title": "Confirmer les salons",
                                           "assignee_id": "abraham", "due_date": "2020-01-01"})
    depts = {d["role"]: d for d in (await mohamed.get("/api/space")).json()["departments"]}
    assert depts["growth"]["head_id"] == "abraham"
    assert depts["growth"]["overdue"] == 1 and depts["growth"]["late_titles"] == ["Confirmer les salons"]
    assert depts["tech"]["head_id"] == "kevin" and depts["finance"]["head_id"] == "carmel"
