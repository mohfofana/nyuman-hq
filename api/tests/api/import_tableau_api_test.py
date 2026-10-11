from datetime import datetime
from io import BytesIO

from openpyxl import Workbook

from tests.conftest import login

XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def tableau() -> bytes:
    """Un classeur construit comme le tableau de pré-lancement (mêmes onglets, mêmes en-têtes), avec des données inventées."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Suivi des Tâches"
    ws.append(["ID", "Priorité", "Pôle", "Tâche / Action", "Statut", "Date limite", "Liens vers Documents", "Commentaires"])
    ws.append([1, "P0 / Haute", "Technique", "Déployer la bêta sur TestFlight", "À faire", datetime(2026, 10, 22), None, None])
    ws.append([4, "P1 / Haute", "Opérationnel", "Terminer l'offre aux fondateurs", "À faire", "30 sept.", None, "Urgent"])
    ws.append([5, "P1 / Haute", "Marketing", "Onboarding des prestataires", "Terminé", "2026-10-04", None, None])

    ws = wb.create_sheet("Détail - Pôle Opérationnel")
    ws.append(["ID Tâche Parent", "Tâche Parent (Feuille 1)", "Processus / Étape / Sous-tâche", "Responsable",
               "Livrable / Résultat attendu", "Statut", "Date de début", "Échéance / Date limite", "Blocages / Notes / Preuves"])
    ws.append([4, "Terminer l'offre aux fondateurs", "4.1 Finalisation de l'offre", "Awa", "Offre PDF", None, None, None, None])
    ws.append([4, "Terminer l'offre aux fondateurs", "4.2 Validation en interne", None, None, "À faire", None, None, None])
    ws.append([99, "Tâche absente", "99.1 Étape orpheline", None, None, None, None, None, None])

    ws = wb.create_sheet("Décisions pré-lancement et post lancement")
    ws.append(["Date", "Pôle concerné", "Titre", "Sujet  / Demande", "Pôle en charge",
               "Décisions actées / Stipulation du contexte de la demande", "Objectifs", "Liens vers Documents (Drive/Fiches)", "Statut"])
    ws.append(["20/09/2026", "Opérationnel", "Ajourné", "Réunion de lancement", "Opérationnel",
               "Validation du calendrier", None, "[Insérer lien du dossier Drive]", "Validé"])
    ws.append([datetime(2026, 10, 11), "Opérationnel", "Nouveau", "Commission Wave", "Opérationnel, Marketing",
               "Trancher : pro ou Nyuman ?", "Sécuriser la marge", "N/A", "Nouveau"])
    # La même ligne collée deux fois (c'est arrivé dans le vrai tableau) : reprise une seule fois.
    ws.append([datetime(2026, 10, 11), "Opérationnel", "Nouveau", "Commission Wave", "Opérationnel, Marketing",
               "Trancher : pro ou Nyuman ?", "Sécuriser la marge", "N/A", "Nouveau"])

    ws = wb.create_sheet("Gestion du Panel Prestataires")
    ws.append(["Numéro Fondateurs (VIP / Grande audience)", "Catégorie ", "Nom et prénoms ", "Nom d'utilisateur ", "Audience ",
               "Contact ", "Mail accès test ", "Statut Contrat/NDA ", "Accès test "])
    ws.append([1, "Fondateur", "Test Aya", "Salon Test", "30K - 70K", "0700000001", "aya@example.com", "En attente", "Lien test à envoyer"])
    ws.append([2, "Partenaire", "Test Binta", "Binta Braids", "1K - 10K", 700000002, "-", "-", "Lien test à envoyer"])

    ws = wb.create_sheet("Hypotheses")
    ws.append(["Frais NYUMAN", "2% (min 100F)"])
    ws.append(["Ticket moyen barber (FCFA)", 1500])
    ws.append(["Total", "#REF!"])

    wb.create_sheet("Vide")
    buffer = BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


async def envoyer(client, apercu: bool, content: bytes = None, name: str = "NYUMAN APP - PHASE PRE-LANCEMENT.xlsx"):
    return await client.post(
        f"/api/import/tableau?apercu={'true' if apercu else 'false'}",
        files={"fichier": (name, content or tableau(), XLSX)},
    )


async def test_apercu_puis_import_puis_reimport_sans_doublon(client):
    await login(client)
    await client.post("/api/membres", json={"email": "awa@example.com", "name": "Awa Test", "role": "membre"})

    preview = await envoyer(client, apercu=True)
    assert preview.status_code == 200, preview.text
    body = preview.json()
    counts = {l["contenu"]: l["nouveaux"] for l in body["lignes"]}
    assert counts == {
        "tâches (salle de projet)": 3,
        "sous-étapes des tâches": 2,
        "sujets de la salle du conseil": 2,
        "fiches du panel des pros": 2,
        "documents de la bibliothèque": 1,
    }
    assert body["onglets"]["Vide"] == "vide, ignoré"
    assert any("orpheline" in w for w in body["avertissements"])
    assert any("Commission Wave" in w and "double" in w for w in body["avertissements"])
    assert (await client.get("/api/taches")).json() == []  # l'aperçu n'écrit rien

    done = await envoyer(client, apercu=False)
    assert done.status_code == 200

    taches = {t["title"]: t for t in (await client.get("/api/taches")).json()}
    offre = taches["Terminer l'offre aux fondateurs"]
    assert offre["priority"] == "P1" and offre["pole"] == "operations" and offre["due_date"] == "2026-09-30"
    assert offre["source"] == "tableau" and "Urgent" in offre["description"]
    assert [e["title"] for e in offre["etapes"]] == ["Finalisation de l'offre", "Validation en interne"]
    assert offre["etapes"][0]["responsable"]["name"] == "Awa Test"
    assert taches["Onboarding des prestataires"]["status"] == "fait"
    assert taches["Déployer la bêta sur TestFlight"]["due_date"] == "2026-10-22"

    sujets = {d["titre"]: d for d in (await client.get("/api/decisions")).json()}
    assert sujets["Réunion de lancement"]["statut"] == "valide"
    assert sujets["Réunion de lancement"]["decision"] == "Validation du calendrier"
    assert sujets["Réunion de lancement"]["liens"] == ""  # le « [Insérer lien …] » n'est pas repris
    assert sujets["Commission Wave"]["statut"] == "nouveau"
    assert sujets["Commission Wave"]["demande"] == "Trancher : pro ou Nyuman ?"
    assert sujets["Commission Wave"]["poles_en_charge"] == ["operations", "croissance"]

    pros = {p["nom"]: p for p in (await client.get("/api/pros")).json()}
    assert pros["Test Aya"]["categorie"] == "fondateur" and pros["Test Aya"]["contrat"] == "en_attente"
    assert pros["Test Aya"]["acces_test"] == "a_envoyer" and pros["Test Aya"]["audience"] == "30K - 70K"
    assert pros["Test Binta"]["email"] == "" and pros["Test Binta"]["telephone"] == "700000002"

    docs = (await client.get("/api/documents")).json()
    hypotheses = next(d for d in docs if d["title"] == "Tableau — Hypotheses")
    assert hypotheses["category"] == "finances"

    feed = (await client.get("/api/evenements")).json()
    assert feed[0]["text"].startswith("a repris le tableau « NYUMAN APP - PHASE PRE-LANCEMENT » : 3 tâches, 2 étapes")

    again = (await envoyer(client, apercu=False)).json()
    assert all(l["nouveaux"] == 0 for l in again["lignes"])
    assert len((await client.get("/api/taches")).json()) == 3


async def test_reserve_aux_heads_et_aux_fichiers_xlsx(client):
    await login(client)
    await client.post("/api/membres", json={"email": "awa@example.com", "name": "Awa", "role": "membre"})
    assert (await envoyer(client, apercu=True, name="tableau.csv")).status_code == 400
    assert (await envoyer(client, apercu=True, content=b"pas un classeur")).status_code == 400

    await login(client, "awa@example.com")
    assert (await envoyer(client, apercu=True)).status_code == 403


async def test_un_classeur_sans_onglet_reconnu_est_refuse(client):
    await login(client)
    wb = Workbook()
    wb.active.append(["Rien", "à voir"])
    buffer = BytesIO()
    wb.save(buffer)
    response = await envoyer(client, apercu=True, content=buffer.getvalue())
    assert response.status_code == 400 and "Aucun onglet reconnu" in response.json()["detail"]
