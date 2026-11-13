async def test_organigramme_12_postes(mohamed):
    org = (await mohamed.get("/api/org")).json()
    assert len(org["positions"]) == 12 and len(org["departments"]) == 5
    p10 = next(p for p in org["positions"] if p["id"] == 10)
    assert p10["reports_to"] == 1 and p10["support_ids"] == ["kodjo", "kwame"] and p10["holder_ids"] == []


async def test_head_place_une_personne(mohamed):
    r = await mohamed.put("/api/org/positions/7", json={"holder_ids": ["sullyvan"], "support_ids": []})
    assert r.status_code == 200
    p7 = next(p for p in r.json()["positions"] if p["id"] == 7)
    assert p7["holder_ids"] == ["sullyvan"]


async def test_un_agent_ne_tient_pas_un_poste(mohamed):
    r = await mohamed.put("/api/org/positions/9", json={"holder_ids": ["adjoua"]})
    assert r.status_code == 400


async def test_non_head_refuse(client):
    from tests.conftest import login_as
    c = await login_as("kevin")
    import app.domain.models as m  # Kevin est head : on vérifie avec un membre non-head créé à la volée
    from app.db import SessionLocal
    async with SessionLocal() as s:
        s.add(m.Member(id="testeur", name="Testeur", kind="human", title="Stagiaire", is_head=False))
        await s.commit()
    t = await login_as("testeur")
    assert (await t.put("/api/org/positions/4", json={"holder_ids": ["testeur"]})).status_code == 403
    await c.aclose(); await t.aclose()
