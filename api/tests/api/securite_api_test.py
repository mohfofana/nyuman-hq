async def test_hq_est_prive_pour_les_moteurs_de_recherche_et_les_autres_sites(client):
    response = await client.get("/api/sante")
    headers = response.headers
    assert headers["x-robots-tag"].startswith("noindex")
    assert headers["x-frame-options"] == "DENY"
    assert headers["x-content-type-options"] == "nosniff"
    assert "frame-ancestors 'none'" in headers["content-security-policy"]
    assert "strict-transport-security" not in headers  # seulement en production, derrière HTTPS
