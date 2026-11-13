async def post(c, channel, body, **kw):
    r = await c.post(f"/api/channels/{channel}/messages", json={"body": body, **kw})
    assert r.status_code == 201, r.text
    return r.json()


async def unread_of(c, channel_id):
    chans = (await c.get("/api/channels")).json()
    return next(ch for ch in chans if ch["id"] == channel_id)


async def test_canaux_de_depart(mohamed):
    names = {c["name"] for c in (await mohamed.get("/api/channels")).json()}
    assert {"général", "tech", "finance", "opérations"} <= names


async def test_message_et_non_lus(mohamed, kevin):
    await kevin.post("/api/channels/general/read")
    await post(mohamed, "general", "Bonjour l'équipe")
    ch = await unread_of(kevin, "general")
    assert ch["unread"] == 1 and ch["mentions"] == 0
    await kevin.post("/api/channels/general/read")
    assert (await unread_of(kevin, "general"))["unread"] == 0


async def test_mention_compte_et_activite(mohamed, kevin):
    await kevin.post("/api/channels/tech/read")
    await post(mohamed, "tech", "<@kevin> tu peux regarder ?")
    assert (await unread_of(kevin, "tech"))["mentions"] == 1
    act = (await kevin.get("/api/activity")).json()
    assert act[0]["kind"] == "mention"


async def test_fil_de_discussion(mohamed, kevin):
    root = await post(mohamed, "general", "Question")
    await post(kevin, "general", "Réponse", parent_id=root["id"])
    msgs = (await mohamed.get("/api/channels/general/messages")).json()
    assert [m["body"] for m in msgs] == ["Question"]  # les réponses restent dans le fil
    assert msgs[0]["reply_count"] == 1 and msgs[0]["reply_authors"] == ["kevin"]
    t = (await mohamed.get(f"/api/messages/{root['id']}/thread")).json()
    assert [m["body"] for m in t["replies"]] == ["Réponse"]
    assert (await mohamed.get("/api/activity")).json()[0]["kind"] == "reply"


async def test_pas_de_fil_dans_un_fil(mohamed):
    root = await post(mohamed, "general", "A")
    reply = await post(mohamed, "general", "B", parent_id=root["id"])
    r = await mohamed.post("/api/channels/general/messages", json={"body": "C", "parent_id": reply["id"]})
    assert r.status_code == 400


async def test_reaction_bascule(mohamed, kevin):
    m = await post(mohamed, "general", "Top")
    r = (await kevin.post(f"/api/messages/{m['id']}/reactions", json={"emoji": "👍"})).json()
    assert r["reactions"] == [{"emoji": "👍", "member_ids": ["kevin"]}]
    r = (await kevin.post(f"/api/messages/{m['id']}/reactions", json={"emoji": "👍"})).json()
    assert r["reactions"] == []


async def test_modifier_supprimer_seulement_auteur(mohamed, kevin):
    m = await post(mohamed, "general", "Brouillon")
    assert (await kevin.patch(f"/api/messages/{m['id']}", json={"body": "x"})).status_code == 403
    r = (await mohamed.patch(f"/api/messages/{m['id']}", json={"body": "Propre"})).json()
    assert r["body"] == "Propre" and r["edited_at"]
    r = (await mohamed.delete(f"/api/messages/{m['id']}")).json()
    assert r["deleted"] and r["body"] == ""


async def test_message_prive_reste_prive(mohamed, kevin, sullyvan):
    dm = (await mohamed.post("/api/dms", json={"member_ids": ["kevin"]})).json()["id"]
    again = (await kevin.post("/api/dms", json={"member_ids": ["mohamed"]})).json()["id"]
    assert dm == again
    await post(mohamed, dm, "Entre nous")
    assert (await kevin.get(f"/api/channels/{dm}/messages")).status_code == 200
    assert (await sullyvan.get(f"/api/channels/{dm}/messages")).status_code == 404
    assert dm not in {c["id"] for c in (await sullyvan.get("/api/channels")).json()}
    assert (await sullyvan.get("/api/search", params={"q": "Entre nous"})).json() == []


async def test_recherche(mohamed):
    await post(mohamed, "finance", "Le plafond d'acompte passe à 40 %")
    found = (await mohamed.get("/api/search", params={"q": "plafond"})).json()
    assert len(found) == 1 and found[0]["channel_id"] == "finance"


async def test_creer_canal(mohamed):
    r = await mohamed.post("/api/channels", json={"name": "#Lancement", "topic": "12/12"})
    assert r.status_code == 201
    assert (await mohamed.post("/api/channels", json={"name": "lancement"})).status_code == 409


async def test_fichier_joint(mohamed, kevin, sullyvan):
    up = (await mohamed.post("/api/uploads", files={"file": ("devis.pdf", b"%PDF-1.4 test", "application/pdf")})).json()
    dm = (await mohamed.post("/api/dms", json={"member_ids": ["kevin"]})).json()["id"]
    m = await post(mohamed, dm, "", attachment_ids=[up["id"]])
    assert m["attachments"][0]["filename"] == "devis.pdf"
    assert (await kevin.get(up["url"])).content == b"%PDF-1.4 test"
    assert (await sullyvan.get(up["url"])).status_code == 404


async def test_message_vide_refuse(mohamed):
    r = await mohamed.post("/api/channels/general/messages", json={"body": "   "})
    assert r.status_code == 400


async def test_lu_en_parallele_sans_erreur(mohamed):
    import asyncio
    rs = await asyncio.gather(*[mohamed.post("/api/channels/general/read") for _ in range(5)])
    assert {r.status_code for r in rs} == {204}
