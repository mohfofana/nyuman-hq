from httpx import ASGITransport, AsyncClient

from app.main import app


def agent_client(agent, **headers):
    return AsyncClient(transport=ASGITransport(app=app, client=("127.0.0.1", 5000)), base_url="http://test",
                       headers={"X-HQ-Agent": agent, **headers})


async def test_agent_ecrit_en_local():
    async with agent_client("kwame") as a:
        assert (await a.get("/api/auth/me")).json()["kind"] == "agent"
        r = await a.post("/api/channels/general/messages", json={"body": "Bonjour, je suis Kwame (agent)."})
        assert r.status_code == 201 and r.json()["author_id"] == "kwame"


async def test_humain_ne_passe_pas_pour_un_agent():
    async with agent_client("mohamed") as a:
        assert (await a.get("/api/auth/me")).status_code == 401


async def test_a_travers_un_tunnel_la_cle_est_obligatoire(mohamed):
    async with agent_client("kwame", **{"Cf-Connecting-Ip": "1.2.3.4"}) as a:
        assert (await a.get("/api/auth/me")).status_code == 401
    token = (await mohamed.post("/api/auth/agents/kwame/token")).json()["token"]
    async with agent_client("kwame", **{"Cf-Connecting-Ip": "1.2.3.4", "Authorization": f"Bearer {token}"}) as a:
        assert (await a.get("/api/auth/me")).json()["id"] == "kwame"
    async with agent_client("koffi", **{"Cf-Connecting-Ip": "1.2.3.4", "Authorization": f"Bearer {token}"}) as a:
        assert (await a.get("/api/auth/me")).status_code == 401  # la clé de Kwame ne marche pas pour Koffi


async def test_seul_un_head_cree_une_cle():
    async with agent_client("kwame") as a:
        assert (await a.post("/api/auth/agents/kwame/token")).status_code == 403


async def test_statut_agent_et_presence():
    from app.realtime import hub
    async with agent_client("koffi") as a:
        r = await a.patch("/api/members/me", json={"manual_status": "blocked", "now_doing": "Attend les chiffres d'Adjoua"})
        assert r.json()["manual_status"] == "blocked"
        assert (await a.patch("/api/members/me", json={"manual_status": "dnd"})).status_code == 400
    assert hub.snapshot("koffi")["connected"] is True
