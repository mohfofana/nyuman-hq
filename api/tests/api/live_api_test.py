from core.realtime.broker import broker
from core.realtime.presence import presence_registry
from tests.conftest import login


async def test_le_fil_part_en_direct_apres_l_enregistrement(client):
    await login(client)
    queue = broker.subscribe()
    try:
        await client.post("/api/documents", json={"title": "Pitch", "category": "pitch", "content": ""})
        messages = [queue.get_nowait() for _ in range(queue.qsize())]
    finally:
        broker.unsubscribe(queue)
    events = [m for m in messages if m["type"] == "evenement"]
    assert [e["text"] for e in events] == ["a créé le document « Pitch »."]
    assert events[0]["link"].startswith("/bibliotheque/")


async def test_dire_ou_l_on_est(client):
    me = await login(client)
    presence_registry.clear()
    presence_registry.connect(me["id"])
    queue = broker.subscribe()
    try:
        response = await client.post(
            "/api/presence", json={"piece": "bibliotheque", "label": "lit « Pitch »", "document_id": 3}
        )
        assert response.status_code == 204
        message = queue.get_nowait()
    finally:
        broker.unsubscribe(queue)
        presence_registry.clear()
    assert message["membre_id"] == me["id"]
    assert message["presence"]["piece"] == "bibliotheque" and message["presence"]["document_id"] == 3


async def test_une_piece_inconnue_est_refusee(client):
    await login(client)
    assert (await client.post("/api/presence", json={"piece": "cave", "label": "x"})).status_code == 422


async def test_le_bureau_montre_les_actions_d_un_seul_membre(client):
    me = await login(client)
    await client.post("/api/documents", json={"title": "Pitch", "category": "pitch", "content": ""})
    mine = (await client.get("/api/evenements", params={"acteur": me["id"]})).json()
    assert mine and all(e["actor"]["id"] == me["id"] for e in mine)
    assert (await client.get("/api/evenements", params={"acteur": 999})).json() == []
