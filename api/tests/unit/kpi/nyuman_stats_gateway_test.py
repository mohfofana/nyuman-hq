import httpx
import pytest

from adapters.common.ports.out.nyuman_stats_gateway import NON_BRANCHEE, NyumanStatsGateway, reset_cache

TOTALS = {
    "utilisateurs_inscrits": 1240,
    "pros_actifs": 38,
    "reservations_7j": 212,
    "acomptes_7j_fcfa": 486000.0,
    "revenu_nyuman_7j_fcfa": 23900.0,
    "genere_le": "2026-10-12T09:00:00Z",
}


@pytest.fixture(autouse=True)
def _clean_cache():
    reset_cache()
    yield
    reset_cache()


async def test_non_branchee_sans_adresse_ni_cle():
    snapshot = await NyumanStatsGateway(None, None).snapshot()
    assert snapshot.available is False and snapshot.reason == NON_BRANCHEE


async def test_lit_les_totaux_avec_la_cle_et_garde_en_cache():
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(200, json=TOTALS)

    gateway = NyumanStatsGateway("https://api.example.com/", "cle", transport=httpx.MockTransport(handler))
    first = await gateway.snapshot()
    second = await gateway.snapshot()

    assert first.value_of("pros_actifs") == 38 and first.value_of("revenu_nyuman_7j_fcfa") == 23900
    assert second is first and len(calls) == 1
    assert str(calls[0].url) == "https://api.example.com/statistiques/hq"
    assert calls[0].headers["X-Stats-Key"] == "cle"


async def test_panne_garde_les_derniers_chiffres_connus():
    responses = iter([httpx.Response(200, json=TOTALS), httpx.Response(503)])
    transport = httpx.MockTransport(lambda request: next(responses))
    gateway = NyumanStatsGateway("https://api.example.com", "cle", cache_seconds=0, transport=transport)

    good = await gateway.snapshot()
    after_failure = await gateway.snapshot()
    assert after_failure.available and after_failure.updated_at == good.updated_at


async def test_panne_sans_chiffres_connus():
    transport = httpx.MockTransport(lambda request: httpx.Response(401))
    snapshot = await NyumanStatsGateway("https://api.example.com", "mauvaise", transport=transport).snapshot()
    assert snapshot.available is False
