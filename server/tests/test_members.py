async def test_liste_humains_et_agents(mohamed):
    r = await mohamed.get("/api/members")
    kinds = {m["kind"] for m in r.json()}
    assert r.status_code == 200 and kinds == {"human", "agent"}


async def test_la_liste_de_l_equipe_n_est_pas_publique(client):
    """Elle porte les noms, les postes et les adresses : hors connexion, rien ne sort."""
    assert (await client.get("/api/members")).status_code == 401


async def test_non_connecte(client):
    assert (await client.get("/api/auth/me")).status_code == 401


async def test_agent_ne_se_connecte_pas_comme_humain(client):
    r = await client.post("/api/auth/dev-login", json={"member_id": "koffi"})
    assert r.status_code == 400


async def test_mettre_a_jour_sa_fiche(mohamed):
    r = await mohamed.patch("/api/members/me", json={"now_doing": "Relit le plan HQ", "manual_status": "busy"})
    assert r.json()["now_doing"] == "Relit le plan HQ"
    assert (await mohamed.get("/api/auth/me")).json()["manual_status"] == "busy"


async def test_statut_inconnu_refuse(mohamed):
    r = await mohamed.patch("/api/members/me", json={"manual_status": "vacances"})
    assert r.status_code == 400


async def test_seed_met_a_jour_les_membres_existants():
    from app.db import SessionLocal
    from app.domain.models import Member
    from app.domain.seed import seed
    async with SessionLocal() as s:
        (await s.get(Member, "kevin")).name = "Ancien nom"
        await s.commit()
        await seed(s)
        assert (await s.get(Member, "kevin")).name == "Kevin Diakité"
