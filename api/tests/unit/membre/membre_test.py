from datetime import datetime, timedelta, timezone

from domain.entities.membre import AGENT, Membre, initiales, nom_depuis_email


def test_nom_provisoire_depuis_l_adresse():
    assert nom_depuis_email("mohamed.fofana@nyuman.app") == "Mohamed Fofana"
    assert nom_depuis_email("chris-sullyvan_koffi@nyuman.app") == "Chris Sullyvan Koffi"
    assert initiales(nom_depuis_email("mohamed.fofana@nyuman.app")) == "MF"


def test_initiales():
    assert initiales("Chris-Sullyvan Koffi") == "CK"
    assert initiales("Kevin") == "K"
    assert initiales("Chef de cabinet") == "CC"
    assert initiales("") == "?"


def test_presence_d_un_humain():
    now = datetime(2026, 10, 12, 10, 0, tzinfo=timezone.utc)
    membre = Membre(name="Kevin", last_seen_at=now - timedelta(minutes=3))
    assert membre.current_status(now) == "en_ligne"
    membre.last_seen_at = now - timedelta(minutes=20)
    assert membre.current_status(now) == "absent"


def test_un_agent_garde_son_statut_de_travail():
    agent = Membre(name="Prospection", kind=AGENT, status="bloque")
    assert agent.current_status(datetime.now(timezone.utc)) == "bloque"
    assert agent.is_head is False
