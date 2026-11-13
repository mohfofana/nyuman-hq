async def new_project(c, name="Lancement 12/12"):
    r = await c.post("/api/projects", json={"name": name, "icon": "🚀", "department": "Croissance"})
    assert r.status_code == 201, r.text
    return r.json()


async def test_projet_et_compteurs(mohamed):
    p = await new_project(mohamed)
    await mohamed.post("/api/tasks", json={"project_id": p["id"], "title": "Liste des salons", "status": "doing"})
    await mohamed.post("/api/tasks", json={"project_id": p["id"], "title": "Affiches"})
    lst = (await mohamed.get("/api/projects")).json()
    assert lst[0]["counts"] == {"doing": 1, "todo": 1}


async def test_tache_terminee_date_et_filtre(mohamed, kevin):
    p = await new_project(mohamed)
    t = (await mohamed.post("/api/tasks", json={"project_id": p["id"], "title": "Brancher Google", "assignee_id": "kevin",
                                                 "due_date": "2026-11-20", "priority": "high"})).json()
    assert t["due_date"] == "2026-11-20" and t["completed_at"] is None
    done = (await kevin.patch(f"/api/tasks/{t['id']}", json={"status": "done"})).json()
    assert done["completed_at"] and done["updated_by"] == "kevin"
    recent = (await mohamed.get("/api/tasks", params={"assignee_id": "kevin", "done_since_days": 7})).json()
    assert [x["id"] for x in recent] == [t["id"]]
    back = (await kevin.patch(f"/api/tasks/{t['id']}", json={"status": "doing"})).json()
    assert back["completed_at"] is None


async def test_valeurs_refusees(mohamed):
    p = await new_project(mohamed)
    assert (await mohamed.post("/api/tasks", json={"project_id": p["id"], "title": "x", "status": "fini"})).status_code == 400
    assert (await mohamed.post("/api/tasks", json={"project_id": p["id"], "title": "x", "assignee_id": "inconnu"})).status_code == 400
    assert (await mohamed.post("/api/tasks", json={"project_id": "nope", "title": "x"})).status_code == 404


async def test_pages_arborescence_et_recherche(mohamed, kevin):
    p = await new_project(mohamed)
    root = (await mohamed.post(f"/api/projects/{p['id']}/pages", json={"title": "Plan de lancement"})).json()
    child = (await mohamed.post(f"/api/projects/{p['id']}/pages", json={"title": "Budget", "parent_id": root["id"]})).json()
    assert child["parent_id"] == root["id"]
    r = (await kevin.patch(f"/api/pages/{root['id']}", json={"content": '{"type":"doc"}', "text": "Brunch des pros le 12 décembre"})).json()
    assert r["updated_by"] == "kevin"
    found = (await mohamed.get("/api/projects-search", params={"q": "brunch"})).json()
    assert [x["id"] for x in found["pages"]] == [root["id"]]
    assert (await mohamed.patch(f"/api/pages/{root['id']}", json={"parent_id": root["id"]})).status_code == 400
    await mohamed.patch(f"/api/pages/{child['id']}", json={"archived": True})
    pages = (await mohamed.get(f"/api/projects/{p['id']}/pages")).json()
    assert [x["id"] for x in pages] == [root["id"]]
