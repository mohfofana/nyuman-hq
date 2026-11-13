from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.api.timesheet import send_time_asks, today_local
from app.db import SessionLocal
from app.domain.models import Message, TimeAsk


async def new_project(c, name="Lancement 12/12", budget=None):
    p = (await c.post("/api/projects", json={"name": name})).json()
    if budget:
        await c.patch(f"/api/projects/{p['id']}", json={"hours_budget": budget})
    return p


async def test_saisie_par_tache_et_ma_semaine(mohamed):
    p = await new_project(mohamed)
    t = (await mohamed.post("/api/tasks", json={"project_id": p["id"], "title": "Affiches", "assignee_id": "mohamed",
                                                 "status": "doing"})).json()
    day = str(today_local())
    sug = (await mohamed.get("/api/time/suggestions")).json()
    assert sug["tasks"][0]["id"] == t["id"] and sug["projects"][0]["id"] == p["id"]
    r = await mohamed.post("/api/time", json={"day": day, "task_id": t["id"], "minutes": 90, "note": "maquette"})
    assert r.status_code == 201, r.text
    e = r.json()
    assert e["project_id"] == p["id"] and e["task_title"] == "Affiches"
    mine = (await mohamed.get("/api/time/me")).json()
    assert [x["minutes"] for x in mine["entries"]] == [90]
    assert (await mohamed.patch(f"/api/time/{e['id']}", json={"minutes": 60})).json()["minutes"] == 60


async def test_refus(mohamed, kevin):
    p = await new_project(mohamed)
    day = str(today_local())
    assert (await mohamed.post("/api/time", json={"day": day, "minutes": 30})).status_code == 400
    futur = str(today_local() + timedelta(days=1))
    assert (await mohamed.post("/api/time", json={"day": futur, "project_id": p["id"], "minutes": 30})).status_code == 400
    e = (await mohamed.post("/api/time", json={"day": day, "project_id": p["id"], "minutes": 30})).json()
    # personne ne modifie la saisie d'un autre
    assert (await kevin.delete(f"/api/time/{e['id']}")).status_code == 404


async def test_vue_equipe_par_personne_reservee_aux_heads(mohamed):
    p = await new_project(mohamed, budget=10)
    day = str(today_local())
    await mohamed.post("/api/time", json={"day": day, "project_id": p["id"], "minutes": 120})
    team = (await mohamed.get("/api/time/team")).json()
    proj = next(x for x in team["projects"] if x["id"] == p["id"])
    assert proj["minutes"] == 120 and proj["budget_pct"] == 20
    assert team["people"][0]["member_id"] == "mohamed"
    # les agents n'ont pas la vue par personne
    from httpx import ASGITransport, AsyncClient
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", headers={"X-HQ-Agent": "adjoua"}) as a:
        r = (await a.get("/api/time/team")).json()
    assert r["people"] is None


async def test_alerte_budget_80_pourcent(mohamed):
    p = await new_project(mohamed, budget=2)
    day = str(today_local())
    await mohamed.post("/api/time", json={"day": day, "project_id": p["id"], "minutes": 60})
    await mohamed.post("/api/time", json={"day": day, "project_id": p["id"], "minutes": 40})  # 100 min = 83 %
    async with SessionLocal() as s:
        bodies = (await s.scalars(select(Message.body).where(Message.author_id == "mariam"))).all()
    assert len(bodies) == 1 and "80 %" in bodies[0]


async def test_question_du_soir_une_seule_fois(mohamed):
    # vendredi 13/11/2026 à 19 h 30 (Abidjan = UTC)
    soir = datetime(2026, 11, 13, 19, 30, tzinfo=timezone.utc)
    asked = await send_time_asks(soir)
    assert "mohamed" in asked and "kodjo" not in asked
    assert "mohamed" not in await send_time_asks(soir + timedelta(minutes=5))
    # trop tôt ou un dimanche : rien
    assert await send_time_asks(datetime(2026, 11, 16, 10, 0, tzinfo=timezone.utc)) == []
    assert await send_time_asks(datetime(2026, 11, 15, 20, 0, tzinfo=timezone.utc)) == []
    async with SessionLocal() as s:
        a = await s.get(TimeAsk, ("mohamed", soir.date()))
        msg = await s.get(Message, a.message_id)
    assert msg.body == "<temps:2026-11-13>" and msg.author_id == "mariam"


async def test_jours_et_heure_reglables(mohamed):
    r = await mohamed.patch("/api/members/me", json={"work_days": "6,2,9,2", "ask_hour": 21})
    assert r.json()["work_days"] == "2,6" and r.json()["ask_hour"] == 21
    assert (await mohamed.patch("/api/members/me", json={"ask_hour": 3})).status_code == 400
    assert (await mohamed.patch("/api/members/me", json={"ask_hour": None})).json()["ask_hour"] is None
