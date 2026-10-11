import re
from datetime import datetime, timedelta, timezone

from sqlalchemy import update

from adapters.core.lien.entity.lien_entity import LienEntity
from tests.conftest import HEAD_EMAIL, login


def jeton_de(mail: dict) -> str:
    match = re.search(r"/connexion#jeton=([A-Za-z0-9_-]+)", mail["text"])
    assert match, mail["text"]
    return match.group(1)


async def demander(client, email: str = HEAD_EMAIL):
    response = await client.post("/api/auth/lien", json={"email": email})
    assert response.status_code == 204, response.text
    return response


async def test_un_lien_ouvre_la_session_une_seule_fois(client, mails):
    await demander(client, HEAD_EMAIL.upper())
    assert len(mails.sent) == 1
    mail = mails.sent[0]
    assert mail["to"] == HEAD_EMAIL
    assert mail["subject"] == "Ton lien pour entrer dans Nyuman HQ"
    assert "http://localhost:5173/connexion#jeton=" in mail["text"] and "Entrer dans HQ" in mail["html"]

    jeton = jeton_de(mail)
    response = await client.post("/api/auth/lien/valider", json={"jeton": jeton})
    assert response.status_code == 200
    assert response.json()["email"] == HEAD_EMAIL
    assert (await client.get("/api/auth/me")).status_code == 200

    feed = (await client.get("/api/evenements")).json()
    assert feed[0]["text"] == "est entré dans la maison pour la première fois."

    await client.post("/api/auth/logout")
    again = await client.post("/api/auth/lien/valider", json={"jeton": jeton})
    assert again.status_code == 401
    assert "plus valable" in again.json()["detail"]


async def test_une_adresse_inconnue_recoit_la_meme_reponse_mais_aucun_email(client, mails):
    await demander(client, "inconnu@example.com")
    assert mails.sent == []


async def test_un_compte_desactive_ne_recoit_pas_de_lien(client, mails):
    await login(client)
    added = await client.post("/api/membres", json={"email": "awa@example.com", "name": "Awa", "role": "membre"})
    await client.patch(f"/api/membres/{added.json()['id']}", json={"active": False})
    await client.post("/api/auth/logout")

    await demander(client, "awa@example.com")
    assert mails.sent == []


async def test_un_lien_expire_ou_faux_est_refuse(client, mails, session_factory):
    await demander(client)
    jeton = jeton_de(mails.sent[0])
    async with session_factory() as session:
        await session.execute(update(LienEntity).values(expires_at=datetime.now(timezone.utc) - timedelta(seconds=1)))
        await session.commit()

    assert (await client.post("/api/auth/lien/valider", json={"jeton": jeton})).status_code == 401
    assert (await client.post("/api/auth/lien/valider", json={"jeton": "x" * 43})).status_code == 401


async def test_pas_plus_de_trois_liens_par_quart_d_heure(client, mails):
    for _ in range(5):
        await demander(client)
    assert len(mails.sent) == 3


async def test_un_lien_utilise_annule_les_autres(client, mails):
    await demander(client)
    await demander(client)
    premier, second = (jeton_de(m) for m in mails.sent)

    assert (await client.post("/api/auth/lien/valider", json={"jeton": second})).status_code == 200
    assert (await client.post("/api/auth/lien/valider", json={"jeton": premier})).status_code == 401


async def test_sans_boite_mail_la_connexion_par_email_est_fermee(client, mails):
    mails.is_configured = False
    assert (await client.get("/api/auth/config")).json()["email_login"] is False
    assert (await client.post("/api/auth/lien", json={"email": HEAD_EMAIL})).status_code == 404


async def test_le_jeton_n_est_jamais_garde_en_clair(client, mails, session_factory):
    await demander(client)
    jeton = jeton_de(mails.sent[0])
    async with session_factory() as session:
        stored = (await session.execute(LienEntity.__table__.select())).mappings().one()
    assert stored["token_hash"] != jeton and len(stored["token_hash"]) == 64
