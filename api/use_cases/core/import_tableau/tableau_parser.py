"""Lecture du tableau de pré-lancement (Google Sheets) : on reconnaît les onglets et les colonnes par leur nom,
pas par leur position, pour que le tableau puisse bouger un peu sans casser la reprise."""

import hashlib
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from use_cases.common.ports.out.tableur_reader import Classeur

ERREURS = ("#REF!", "#ERROR!", "#VALUE!", "#DIV/0!", "#N/A", "#NAME?", "#NUM!")
_MOIS = {
    "janv": 1, "jan": 1, "fevr": 2, "fev": 2, "mars": 3, "mar": 3, "avr": 4, "avril": 4, "mai": 5, "juin": 6,
    "juil": 7, "aout": 8, "sept": 9, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


def norm(value: Any) -> str:
    """« Tâche / Action » → « tache / action » : sans accents, en minuscules, espaces simples."""
    text = unicodedata.normalize("NFKD", str(value or "")).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", text).strip().lower()


def texte(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    if isinstance(value, datetime):
        return value.strftime("%d/%m/%Y")
    if isinstance(value, date):
        return value.strftime("%d/%m/%Y")
    text = str(value).strip()
    return "" if text in ("-", "—", "N/A", "n/a") else text


def empreinte(*parts: Any) -> str:
    return hashlib.sha1("|".join(norm(p) for p in parts).encode()).hexdigest()[:12]


def lire_date(value: Any, annee: int) -> Optional[date]:
    """Dates du tableau : vraies dates, « 2026-10-22 », « 20/09/2026 », « 25 oct. » (année en cours si absente)."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = norm(value)
    if not text:
        return None
    try:
        if m := re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", text):
            return date(int(m[1]), int(m[2]), int(m[3]))
        if m := re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{2,4})", text):
            year = int(m[3]) + (2000 if len(m[3]) == 2 else 0)
            return date(year, int(m[2]), int(m[1]))
        if m := re.fullmatch(r"(\d{1,2})\s+([a-z]+)\.?(?:\s+(\d{4}))?", text):
            mois = _MOIS.get(m[2]) or _MOIS.get(m[2][:4]) or _MOIS.get(m[2][:3])
            if mois:
                return date(int(m[3]) if m[3] else annee, mois, int(m[1]))
    except ValueError:
        return None
    return None


def lire_pole(value: Any) -> str:
    text = norm(value)
    if "techni" in text or "produit" in text or "tech" == text:
        return "produit"
    if "marketing" in text or "croissance" in text or "commercial" in text:
        return "croissance"
    if "operation" in text:
        return "operations"
    if "direction" in text or "ceo" in text:
        return "direction"
    return ""


def lire_poles(value: Any) -> List[str]:
    poles = [lire_pole(part) for part in re.split(r",|/|\bet\b|&|\+", norm(value))]
    return list(dict.fromkeys(p for p in poles if p))


def lire_statut_tache(value: Any) -> str:
    text = norm(value)
    if text.startswith("termin") or text in ("fait", "fini", "ok"):
        return "fait"
    if "cours" in text:
        return "en_cours"
    if "attente" in text or "bloqu" in text:
        return "en_attente"
    return "a_faire"


def lire_statut_etape(value: Any) -> str:
    statut = lire_statut_tache(value)
    return "a_faire" if statut == "en_attente" else statut


def lire_statut_decision(value: Any) -> Optional[str]:
    text = norm(value)
    for key, statut in (("valid", "valide"), ("refus", "refuse"), ("ajourn", "ajourne"), ("initier", "a_initier"),
                        ("cours", "en_cours"), ("nouveau", "nouveau")):
        if key in text:
            return statut
    return None


def lire_priorite(value: Any) -> str:
    m = re.search(r"p\s*([0-3])", norm(value))
    return f"P{m[1]}" if m else ""


def liens_utiles(*values: Any) -> str:
    """Garde les vraies adresses, oublie les « [Insérer lien …] » restés dans le tableau."""
    found: List[str] = []
    for value in values:
        for url in re.findall(r"https?://\S+", str(value or "")):
            if url not in found:
                found.append(url)
    return "\n".join(found)


def premier(*indexes: Optional[int]) -> Optional[int]:
    """Le premier index trouvé (0 compris, contrairement à « a or b »)."""
    return next((i for i in indexes if i is not None), None)


class Colonnes:
    """Repère les colonnes d'un onglet à partir de la ligne d'en-tête."""

    def __init__(self, header: Sequence[Any]):
        self._header = [norm(h) for h in header]

    def index(self, *mots: str, exact: bool = False, sauf: Sequence[str] = ()) -> Optional[int]:
        for i, h in enumerate(self._header):
            if not h or any(s in h for s in sauf):
                continue
            if (exact and h == mots[0]) or (not exact and all(m in h for m in mots)):
                return i
        return None

    @staticmethod
    def get(row: Sequence[Any], i: Optional[int]) -> Any:
        return row[i] if i is not None and i < len(row) else None


def en_tete(rows: List[List[Any]], test: Callable[[Colonnes], bool]) -> Optional[Tuple[int, Colonnes]]:
    for i, row in enumerate(rows[:10]):
        colonnes = Colonnes(row)
        if test(colonnes):
            return i, colonnes
    return None


@dataclass
class TacheLue:
    ref: str
    numero: str
    title: str
    priority: str
    pole: str
    status: str
    due_date: Optional[date]
    description: str


@dataclass
class EtapeLue:
    ref: str
    parent_ref: str
    title: str
    responsable: str
    livrable: str
    status: str
    start_date: Optional[date]
    due_date: Optional[date]
    notes: str


@dataclass
class DecisionLue:
    ref: str
    titre: str
    demande: str
    decision: str
    objectif: str
    liens: str
    pole_concerne: str
    poles_en_charge: List[str]
    statut: str
    date_demande: Optional[date]


@dataclass
class ProLu:
    ref: str
    numero: Optional[int]
    categorie: str
    nom: str
    enseigne: str
    audience: str
    telephone: str
    email: str
    contrat: str
    acces_test: str


@dataclass
class OngletBrut:
    nom: str
    rows: List[List[Any]]


@dataclass
class TableauLu:
    taches: List[TacheLue] = field(default_factory=list)
    etapes: List[EtapeLue] = field(default_factory=list)
    decisions: List[DecisionLue] = field(default_factory=list)
    pros: List[ProLu] = field(default_factory=list)
    autres: List[OngletBrut] = field(default_factory=list)  # deviennent des documents de la bibliothèque
    onglets: Dict[str, str] = field(default_factory=dict)  # nom de l'onglet → ce qu'il est devenu
    avertissements: List[str] = field(default_factory=list)


def _lignes(rows: List[List[Any]], start: int) -> List[List[Any]]:
    return [r for r in rows[start + 1:] if any(texte(c) for c in r)]


def _taches(nom: str, rows: List[List[Any]], annee: int, out: TableauLu) -> bool:
    found = en_tete(rows, lambda c: c.index("id", exact=True) is not None and c.index("tache") is not None)
    if not found:
        return False
    start, c = found
    i_id, i_titre = c.index("id", exact=True), c.index("tache")
    i_prio, i_pole, i_statut = c.index("priorit"), c.index("pole"), c.index("statut")
    i_date, i_liens, i_com = c.index("date"), c.index("lien"), c.index("comment")
    for row in _lignes(rows, start):
        titre = texte(c.get(row, i_titre))
        if not titre:
            continue
        numero = texte(c.get(row, i_id)) or empreinte(titre)
        brut_date = c.get(row, i_date)
        due = lire_date(brut_date, annee)
        if texte(brut_date) and due is None:
            out.avertissements.append(f"Tâche « {titre} » : date « {texte(brut_date)} » non comprise, laissée vide.")
        parties = []
        if com := texte(c.get(row, i_com)):
            parties.append(f"Commentaires : {com}")
        if liens := liens_utiles(c.get(row, i_liens)):
            parties.append(f"Liens :\n{liens}")
        out.taches.append(
            TacheLue(
                ref=f"tableau:tache:{numero}",
                numero=numero,
                title=titre[:200],
                priority=lire_priorite(c.get(row, i_prio)),
                pole=lire_pole(c.get(row, i_pole)),
                status=lire_statut_tache(c.get(row, i_statut)),
                due_date=due,
                description="\n\n".join(parties),
            )
        )
    out.onglets[nom] = "tâches de la salle de projet"
    return True


def _etapes(nom: str, rows: List[List[Any]], annee: int, out: TableauLu) -> bool:
    found = en_tete(rows, lambda c: c.index("parent") is not None and (c.index("etape") is not None or c.index("processus") is not None))
    if not found:
        return False
    start, c = found
    i_parent = c.index("id", "parent")
    i_titre = premier(c.index("processus"), c.index("etape"))
    i_resp, i_livrable, i_statut = c.index("responsable"), c.index("livrable"), c.index("statut")
    i_debut, i_fin, i_notes = c.index("debut"), premier(c.index("limite"), c.index("echeance")), premier(c.index("blocage"), c.index("note"))
    for row in _lignes(rows, start):
        brut = texte(c.get(row, i_titre))
        parent = texte(c.get(row, i_parent))
        if not brut or not parent:
            continue
        m = re.match(r"^(\d+(?:\.\d+)+)\s*[-–:.]?\s*(.*)$", brut)
        code, titre = (m[1], m[2] or brut) if m else (None, brut)
        out.etapes.append(
            EtapeLue(
                ref=f"tableau:etape:{code or parent + '-' + empreinte(titre)}",
                parent_ref=f"tableau:tache:{parent}",
                title=titre[:200],
                responsable=texte(c.get(row, i_resp)),
                livrable=texte(c.get(row, i_livrable)),
                status=lire_statut_etape(c.get(row, i_statut)),
                start_date=lire_date(c.get(row, i_debut), annee),
                due_date=lire_date(c.get(row, i_fin), annee),
                notes=texte(c.get(row, i_notes)),
            )
        )
    out.onglets[nom] = "sous-étapes des tâches"
    return True


def _decisions(nom: str, rows: List[List[Any]], annee: int, out: TableauLu) -> bool:
    found = en_tete(rows, lambda c: c.index("sujet") is not None and c.index("statut") is not None)
    if not found:
        return False
    start, c = found
    i_date, i_concerne, i_titre = c.index("date", exact=True), c.index("pole", "concerne"), c.index("titre")
    i_sujet, i_charge = c.index("sujet"), c.index("pole", "charge")
    i_acte, i_obj = premier(c.index("actee"), c.index("stipulation")), c.index("objectif")
    i_liens, i_statut = c.index("lien"), c.index("statut")
    for row in _lignes(rows, start):
        sujet, titre_col = texte(c.get(row, i_sujet)), texte(c.get(row, i_titre))
        # Dans le tableau, la colonne « Titre » contient souvent un statut (« Ajourné », « Nouveau ») : on prend le sujet.
        titre = sujet or ("" if lire_statut_decision(titre_col) else titre_col)
        if not titre:
            continue
        statut = lire_statut_decision(c.get(row, i_statut)) or lire_statut_decision(titre_col) or "nouveau"
        acte = texte(c.get(row, i_acte))
        tranche = statut in ("valide", "refuse", "ajourne")
        brut_date = c.get(row, i_date)
        jour = lire_date(brut_date, annee)
        out.decisions.append(
            DecisionLue(
                ref=f"tableau:decision:{empreinte(jour.isoformat() if jour else texte(brut_date), sujet or titre)}",
                titre=titre[:200],
                demande="" if tranche else acte,
                decision=acte if tranche else "",
                objectif=texte(c.get(row, i_obj)),
                liens=liens_utiles(c.get(row, i_liens)),
                pole_concerne=lire_pole(c.get(row, i_concerne)),
                poles_en_charge=lire_poles(c.get(row, i_charge)),
                statut=statut,
                date_demande=jour,
            )
        )
    out.onglets[nom] = "sujets de la salle du conseil"
    return True


def _categorie(value: Any) -> str:
    text = norm(value)
    for key, categorie in (("fondateur", "fondateur"), ("ambassad", "ambassadeur"), ("partenaire", "partenaire")):
        if key in text:
            return categorie
    return "prospect"


def _contrat(value: Any) -> str:
    text = norm(value)
    for key, statut in (("attente", "en_attente"), ("sign", "signe"), ("envoyer", "a_envoyer"), ("pas", "non_requis"), ("non", "non_requis")):
        if key in text:
            return statut
    return ""


def _acces(value: Any) -> str:
    text = norm(value)
    for key, statut in (("a envoyer", "a_envoyer"), ("envoye", "envoye"), ("install", "installe"), ("actif", "actif"), ("teste", "actif")):
        if key in text:
            return statut
    return ""


def _telephone(value: Any) -> str:
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return re.sub(r"[^\d+ ]", "", texte(value)).strip()


def _pros(nom: str, rows: List[List[Any]], annee: int, out: TableauLu) -> bool:
    found = en_tete(rows, lambda c: c.index("prenom") is not None and c.index("categorie") is not None)
    if not found:
        return False
    start, c = found
    i_num, i_cat, i_nom = c.index("numero"), c.index("categorie"), c.index("prenom")
    i_enseigne, i_audience = c.index("utilisateur"), c.index("audience", sauf=("numero",))
    i_tel = premier(c.index("contact"), c.index("telephone"))
    i_mail, i_contrat, i_acces = c.index("mail"), c.index("contrat"), c.index("acces", sauf=("mail",))
    for row in _lignes(rows, start):
        nom_pro = texte(c.get(row, i_nom))
        if not nom_pro:
            continue
        brut_num = texte(c.get(row, i_num))
        numero = int(brut_num) if brut_num.isdigit() else None
        email = texte(c.get(row, i_mail)).lower()
        if email and "@" not in email:
            out.avertissements.append(f"Pro « {nom_pro} » : adresse « {email} » non valable, laissée vide.")
            email = ""
        out.pros.append(
            ProLu(
                ref=f"tableau:pro:{numero if numero is not None else empreinte(nom_pro)}",
                numero=numero,
                categorie=_categorie(c.get(row, i_cat)),
                nom=nom_pro[:120],
                enseigne=texte(c.get(row, i_enseigne))[:120],
                audience=texte(c.get(row, i_audience))[:40],
                telephone=_telephone(c.get(row, i_tel))[:40],
                email=email[:254],
                contrat=_contrat(c.get(row, i_contrat)),
                acces_test=_acces(c.get(row, i_acces)),
            )
        )
    out.onglets[nom] = "panel des pros"
    return True


def lire_tableau(classeur: Classeur, annee: int) -> TableauLu:
    out = TableauLu()
    for nom, rows in classeur.items():
        n = norm(nom)
        lu = False
        if "panel" in n or "prestataire" in n:
            lu = _pros(nom, rows, annee, out)
        elif "decision" in n:
            lu = _decisions(nom, rows, annee, out)
        elif n.startswith("detail") or "sous-tache" in n:
            lu = _etapes(nom, rows, annee, out)
        elif "tache" in n:
            lu = _taches(nom, rows, annee, out)
        if not lu:
            if any(texte(cell) for row in rows for cell in row):
                out.autres.append(OngletBrut(nom=nom, rows=rows))
                out.onglets[nom] = "document de la bibliothèque"
            else:
                out.onglets[nom] = "vide, ignoré"
    return out


def en_markdown(onglet: OngletBrut, source: str, jour: date) -> Tuple[str, bool]:
    """Copie figée d'un onglet en tableau Markdown. Renvoie aussi s'il contenait des cellules en erreur."""
    rows = [[texte(c).replace("\n", " — ").replace("|", "\\|") for c in r] for r in onglet.rows]
    rows = [r for r in rows if any(r)]
    width = max((len(r) for r in rows), default=0)
    rows = [r + [""] * (width - len(r)) for r in rows]
    keep = [j for j in range(width) if any(r[j] for r in rows)]
    rows = [[r[j] for j in keep] for r in rows]
    erreurs = any(cell in ERREURS for r in rows for cell in r)

    lines = [
        f"> Copie de l’onglet « {onglet.nom} » du tableau « {source} », reprise le {jour.strftime('%d/%m/%Y')}.",
        "> Les formules ne sont pas reprises : ce sont les valeurs de ce jour-là.",
    ]
    if erreurs:
        lines.append("> **Attention** : certaines cellules étaient en erreur dans le tableau (#REF!, #ERROR!…). À corriger dans le modèle.")
    lines.append("")
    if rows and keep:
        lines.append("| " + " | ".join(rows[0]) + " |")
        lines.append("|" + "---|" * len(keep))
        lines.extend("| " + " | ".join(r) + " |" for r in rows[1:])
    return "\n".join(lines) + "\n", erreurs
