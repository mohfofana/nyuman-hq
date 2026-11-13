from datetime import datetime, timedelta, timezone

from app.api.meetings import members_in_meeting, refresh_presence, send_reminders
from app.db import SessionLocal
from app.realtime import hub


def iso(dt):
    return dt.isoformat()


def soon(minutes=60, length=30):
    start = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    return iso(start), iso(start + timedelta(minutes=length))


async def create(c, **kw):
    start, end = soon()
    body = {"title": "Point du lundi", "start_at": start, "end_at": end, "attendee_ids": ["kevin"], **kw}
    r = await c.post("/api/meetings", json=body)
    assert r.status_code == 201, r.text
    return r.json()


async def test_creer_avec_lien_jitsi(mohamed):
    m = await create(mohamed)
    assert m["link"].startswith("https://meet.jit.si/Nyuman-PointDuLundi-")
    who = {a["member_id"]: a["response"] for a in m["attendees"]}
    assert who == {"mohamed": "yes", "kevin": "pending"}


async def test_google_meet_pas_encore_branche(mohamed):
    start, end = soon()
    r = await mohamed.post("/api/meetings", json={"title": "x", "start_at": start, "end_at": end, "link_kind": "meet"})
    assert r.status_code == 400 and "Jitsi" in r.json()["detail"]
    assert (await mohamed.get("/api/meetings/config")).json() == {"google_meet": False, "jitsi": True}


async def test_fin_avant_debut_refusee(mohamed):
    start, end = soon()
    r = await mohamed.post("/api/meetings", json={"title": "x", "start_at": end, "end_at": start})
    assert r.status_code == 400


async def test_repondre_et_agenda(mohamed, kevin):
    m = await create(mohamed)
    r = (await kevin.post(f"/api/meetings/{m['id']}/respond", json={"response": "yes"})).json()
    assert {a["member_id"]: a["response"] for a in r["attendees"]}["kevin"] == "yes"
    now = datetime.now(timezone.utc)
    lst = (await kevin.get("/api/meetings", params={"start": iso(now), "end": iso(now + timedelta(days=1))})).json()
    assert [x["id"] for x in lst] == [m["id"]]
    up = (await kevin.get("/api/meetings/upcoming")).json()
    assert up[0]["id"] == m["id"]


async def test_seul_organisateur_modifie_ou_annule(mohamed, kevin):
    m = await create(mohamed)
    assert (await kevin.patch(f"/api/meetings/{m['id']}", json={"title": "x"})).status_code == 403
    assert (await kevin.post(f"/api/meetings/{m['id']}/cancel")).status_code == 403
    assert (await mohamed.post(f"/api/meetings/{m['id']}/cancel")).json()["cancelled"] is True


async def test_annonce_dans_le_canal(mohamed):
    m = await create(mohamed, channel_id="general")
    msgs = (await mohamed.get("/api/channels/general/messages")).json()
    assert msgs[-1]["body"] == f"<meeting:{m['id']}>"


async def test_en_reunion_pendant_le_creneau(mohamed, kevin):
    start = datetime.now(timezone.utc) - timedelta(minutes=5)
    r = await mohamed.post("/api/meetings", json={"title": "En cours", "start_at": iso(start),
                                                  "end_at": iso(start + timedelta(minutes=30)), "attendee_ids": ["kevin"]})
    async with SessionLocal() as s:
        who = await members_in_meeting(s, datetime.now(timezone.utc))
    assert who == {"mohamed"}  # Kevin n'a pas encore accepté
    await kevin.post(f"/api/meetings/{r.json()['id']}/join")
    await refresh_presence()
    assert hub.snapshot("kevin")["in_meeting"] is True
    async with SessionLocal() as s:
        later = await members_in_meeting(s, datetime.now(timezone.utc) + timedelta(hours=1))
    assert later == set()


async def test_rappel_envoye_une_fois(mohamed):
    start = datetime.now(timezone.utc) + timedelta(minutes=8)
    r = await mohamed.post("/api/meetings", json={"title": "Bientôt", "start_at": iso(start),
                                                  "end_at": iso(start + timedelta(minutes=30)), "reminder_minutes": 10})
    mid = r.json()["id"]
    assert mid in await send_reminders()
    assert mid not in await send_reminders()


async def test_compte_rendu(mohamed, kevin):
    m = await create(mohamed, channel_id="tech")
    assert (await kevin.post(f"/api/meetings/{m['id']}/notes/publish")).status_code == 400
    r = (await kevin.put(f"/api/meetings/{m['id']}/notes", json={"notes": "- Décision : on garde Jitsi"})).json()
    assert r["notes_by"] == "kevin"
    assert (await kevin.post(f"/api/meetings/{m['id']}/notes/publish")).json() == {"channel_id": "tech"}
    last = (await kevin.get("/api/channels/tech/messages")).json()[-1]
    assert "Compte rendu" in last["body"] and "Jitsi" in last["body"]
