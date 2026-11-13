from app.api import appstats
from app.config import settings

SAMPLE = {"growth": {"pros_total": 12, "pros_active": 10, "pros_with_completed": 5, "new_pros_7d": 2}}


async def test_pas_branche(mohamed, monkeypatch):
    monkeypatch.setattr(settings, "stats_url", "")
    r = (await mohamed.get("/api/app-stats")).json()
    assert r == {"available": False, "reason": "not_configured"}


async def test_branche_avec_cache_et_secours(mohamed, monkeypatch):
    monkeypatch.setattr(settings, "stats_url", "https://api.test/admin/hq-stats")
    monkeypatch.setattr(settings, "stats_key", "cle-de-test")
    appstats.reset_cache()
    calls = []

    async def fake():
        calls.append(1)
        return SAMPLE
    monkeypatch.setattr(appstats, "fetch_stats", fake)
    assert (await mohamed.get("/api/app-stats")).json()["stats"] == SAMPLE
    await mohamed.get("/api/app-stats")
    assert len(calls) == 1  # 5 minutes de cache

    async def down():
        raise RuntimeError("injoignable")
    monkeypatch.setattr(appstats, "fetch_stats", down)
    appstats._cache["at"] = 0
    r = (await mohamed.get("/api/app-stats")).json()
    assert r["stale"] is True and r["stats"] == SAMPLE
    appstats.reset_cache()
