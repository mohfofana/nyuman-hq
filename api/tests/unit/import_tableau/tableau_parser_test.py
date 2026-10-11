from datetime import date, datetime

from use_cases.core.import_tableau.tableau_parser import (
    OngletBrut,
    en_markdown,
    lire_date,
    lire_pole,
    lire_poles,
    lire_priorite,
    lire_statut_decision,
    lire_statut_tache,
    liens_utiles,
)


def test_les_dates_du_tableau():
    assert lire_date("2026-10-22", 2026) == date(2026, 10, 22)
    assert lire_date("20/09/2026", 2026) == date(2026, 9, 20)
    assert lire_date("25 oct.", 2026) == date(2026, 10, 25)
    assert lire_date("01 déc.", 2026) == date(2026, 12, 1)
    assert lire_date("30 sept.", 2026) == date(2026, 9, 30)
    assert lire_date(datetime(2026, 11, 5, 0, 0), 2026) == date(2026, 11, 5)
    assert lire_date("bientôt", 2026) is None
    assert lire_date("31/02/2026", 2026) is None


def test_poles_statuts_et_priorites():
    assert lire_pole("Technique") == "produit"
    assert lire_pole("Opérationnel") == "operations"
    assert lire_pole("Marketing") == "croissance"
    assert lire_poles("Opérationnel, Marketing") == ["operations", "croissance"]
    assert lire_statut_tache("Terminé") == "fait"
    assert lire_statut_tache("En cours") == "en_cours"
    assert lire_statut_tache("") == "a_faire"
    assert lire_statut_decision("À initier") == "a_initier"
    assert lire_statut_decision("Validé") == "valide"
    assert lire_statut_decision("Ajourné") == "ajourne"
    assert lire_priorite("P2 / Moyenne") == "P2"
    assert lire_priorite("Haute") == ""


def test_liens_les_emplacements_vides_sont_oublies():
    assert liens_utiles("[Insérer lien du dossier Drive]") == ""
    assert liens_utiles("[Insérer lien]   https://docs.google.com/document/d/abc/edit  ") == "https://docs.google.com/document/d/abc/edit"


def test_un_onglet_devient_un_tableau_markdown_avec_alerte_si_erreurs():
    contenu, erreurs = en_markdown(
        OngletBrut("Jalons", [["Jalon", "Revenu"], ["Mois 6", 67500], [None, None], ["Cumulé", "#REF!"]]),
        "NYUMAN APP",
        date(2026, 10, 11),
    )
    assert erreurs is True
    assert "| Jalon | Revenu |" in contenu and "| Mois 6 | 67500 |" in contenu
    assert "reprise le 11/10/2026" in contenu and "**Attention**" in contenu
