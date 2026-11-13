import asyncio

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.main import app

from app.config import settings
from app.db import SessionLocal
from app.domain.models import AgentRun
from app.wake import waker


@pytest.fixture
def fake_runner(monkeypatch):
    calls = []

    async def runner(agent, model, prompt):
        calls.append((agent, model, prompt))
        await asyncio.sleep(0.05)
        return {"cost": 0.02, "error": ""}

    monkeypatch.setattr(settings, "agent_wake", True)
    monkeypatch.setattr(waker, "runner", runner)
    yield calls
    waker.pending.clear(); waker.busy.clear(); waker.capped_notice.clear()


async def settle():
    for _ in range(80):
        if not waker.tasks:
            return
        await asyncio.sleep(0.02)


async def runs():
    async with SessionLocal() as s:
        return list((await s.scalars(select(AgentRun).order_by(AgentRun.created_at))).all())


async def test_message_prive_reveille_l_agent(mohamed, fake_runner):
    dm = (await mohamed.post("/api/dms", json={"member_ids": ["koffi"]})).json()["id"]
    await mohamed.post(f"/api/channels/{dm}/messages", json={"body": "Koffi, que penses-tu des frais à 1,5 % ?"})
    await settle()
    assert [c[0] for c in fake_runner] == ["koffi"]
    assert fake_runner[0][1] == "claude-opus-4-6" and "Koffi" in fake_runner[0][2] and "1,5 %" in fake_runner[0][2]
    r = await runs()
    assert r[0].status == "done" and r[0].cost_usd == 0.02


async def test_mention_dans_un_canal_et_modele_de_mariam(mohamed, fake_runner):
    await mohamed.post("/api/channels/general/messages", json={"body": "<@mariam> prépare l'ordre du jour"})
    await settle()
    assert fake_runner[0][:2] == ("mariam", "claude-sonnet-5-5")


async def test_message_humain_sans_agent_ne_reveille_personne(mohamed, fake_runner):
    await mohamed.post("/api/channels/general/messages", json={"body": "<@kevin> bonjour"})
    await settle()
    assert fake_runner == []


async def test_un_agent_ne_reveille_pas_un_autre_agent(fake_runner):
    from tests.test_agents import agent_client
    async with agent_client("kwame") as a:
        await a.post("/api/channels/general/messages", json={"body": "<@koffi> tu peux relire ?"})
    await settle()
    assert fake_runner == []


async def test_plafond_par_jour(mohamed, fake_runner, monkeypatch):
    monkeypatch.setattr(settings, "agent_daily_cap", 1)
    dm = (await mohamed.post("/api/dms", json={"member_ids": ["adjoua"]})).json()["id"]
    await mohamed.post(f"/api/channels/{dm}/messages", json={"body": "un"})
    await settle()
    await mohamed.post(f"/api/channels/{dm}/messages", json={"body": "deux"})
    await settle()
    assert len(fake_runner) == 1
    assert [r.status for r in await runs()] == ["done", "capped"]
    last = (await mohamed.get(f"/api/channels/{dm}/messages")).json()[-1]
    assert last["author_id"] == "adjoua" and "limite" in last["body"]


async def test_messages_rapproches_regroupes(mohamed, fake_runner):
    dm = (await mohamed.post("/api/dms", json={"member_ids": ["kodjo"]})).json()["id"]
    for t in ("a", "b", "c"):
        await mohamed.post(f"/api/channels/{dm}/messages", json={"body": t})
    await settle()
    assert len(fake_runner) <= 2  # le premier réveil, puis un seul pour les messages arrivés pendant


async def test_discussion_ouverte_repond_elle_meme(mohamed, fake_runner, monkeypatch):
    """Kwame a sa discussion Claude ouverte : si elle répond dans les 3 minutes, aucune copie ne part."""
    monkeypatch.setattr(settings, "agent_wake_skip", "kwame")
    monkeypatch.setattr(settings, "agent_wake_grace_s", 0.15)
    dm = (await mohamed.post("/api/dms", json={"member_ids": ["kwame"]})).json()["id"]
    await mohamed.post(f"/api/channels/{dm}/messages", json={"body": "Kwame, la vue téléphone est à revoir."})
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", headers={"X-HQ-Agent": "kwame"}) as k:
        await k.post(f"/api/channels/{dm}/messages", json={"body": "C'est corrigé, je vous envoie une capture."})
    await settle()
    assert fake_runner == []
    # Les autres agents gardent le réveil immédiat.
    autre = (await mohamed.post("/api/dms", json={"member_ids": ["koffi"]})).json()["id"]
    await mohamed.post(f"/api/channels/{autre}/messages", json={"body": "Koffi, votre avis ?"})
    await settle()
    assert [c[0] for c in fake_runner] == ["koffi"]


async def test_filet_de_securite_si_personne_ne_repond(mohamed, fake_runner, monkeypatch):
    """Fenêtre fermée : après le délai de grâce, la copie prend le relais."""
    monkeypatch.setattr(settings, "agent_wake_skip", "kwame")
    monkeypatch.setattr(settings, "agent_wake_grace_s", 0.15)
    dm = (await mohamed.post("/api/dms", json={"member_ids": ["kwame"]})).json()["id"]
    await mohamed.post(f"/api/channels/{dm}/messages", json={"body": "Kwame, vous êtes là ?"})
    await settle()
    assert [c[0] for c in fake_runner] == ["kwame"]
