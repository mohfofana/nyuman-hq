import re
from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Optional

from core.exceptions import BusinessException
from domain.entities.document import Document, DocumentVersion
from domain.entities.evenement import Evenement
from domain.entities.membre import Membre
from use_cases.common.ports.out.tableur_reader import TableurIllisibleException, TableurReader
from use_cases.common.ports.out.transaction import Transaction
from use_cases.core.decision.decision_use_cases import CreateDecisionUseCase, NouvelleDecision
from use_cases.core.decision.repository.decision_repository import DecisionRepository
from use_cases.core.document.repository.document_repository import DocumentRepository
from use_cases.core.etape.etape_use_cases import AddEtapeUseCase, NouvelleEtape
from use_cases.core.etape.repository.etape_repository import EtapeRepository
from use_cases.core.evenement.repository.evenement_repository import EvenementRepository
from use_cases.core.import_tableau.tableau_parser import en_markdown, lire_tableau, norm
from use_cases.core.membre.exceptions.membre_exceptions import ReserveAuxHeadsException
from use_cases.core.membre.repository.membre_repository import MembreRepository
from use_cases.core.pro.pro_use_cases import CreateProUseCase, NouveauPro
from use_cases.core.pro.repository.pro_repository import ProRepository
from use_cases.core.tache.repository.tache_repository import TacheRepository
from use_cases.core.tache.tache_use_cases import CreateTacheUseCase, NouvelleTache

_FINANCES = ("hypoth", "projection", "jalon", "rentab", "charge", "budget", "financ", "treso")


@dataclass
class LigneImport:
    contenu: str
    nouveaux: int = 0
    deja_la: int = 0


@dataclass
class RapportImport:
    apercu: bool
    lignes: List[LigneImport]
    onglets: Dict[str, str]
    avertissements: List[str] = field(default_factory=list)

    @property
    def total_nouveaux(self) -> int:
        return sum(l.nouveaux for l in self.lignes)


def _pluriel(n: int, mot: str) -> str:
    return f"{n} {mot}{'s' if n > 1 else ''}"


class ImportTableauUseCase:
    """Reprend une fois le tableau Google de pré-lancement : tâches et sous-étapes, sujets du conseil, panel des pros.
    Les autres onglets (modèle financier…) deviennent des documents de la bibliothèque.
    Chaque ligne garde un repère : relancer l'import n'ajoute que ce qui manque et ne touche jamais à ce qui existe."""

    def __init__(
        self,
        reader: TableurReader,
        taches: TacheRepository,
        etapes: EtapeRepository,
        decisions: DecisionRepository,
        pros: ProRepository,
        documents: DocumentRepository,
        membres: MembreRepository,
        evenements: EvenementRepository,
        transaction: Transaction,
        create_tache: CreateTacheUseCase,
        add_etape: AddEtapeUseCase,
        create_decision: CreateDecisionUseCase,
        create_pro: CreateProUseCase,
    ):
        self._reader = reader
        self._taches = taches
        self._etapes = etapes
        self._decisions = decisions
        self._pros = pros
        self._documents = documents
        self._membres = membres
        self._evenements = evenements
        self._transaction = transaction
        self._create_tache = create_tache
        self._add_etape = add_etape
        self._create_decision = create_decision
        self._create_pro = create_pro

    async def __call__(self, actor: Membre, content: bytes, nom_fichier: str, apercu: bool, today: Optional[date] = None) -> RapportImport:
        if not actor.is_head:
            raise ReserveAuxHeadsException()
        today = today or date.today()
        lu = lire_tableau(self._reader.read(content), today.year)
        if not (lu.taches or lu.etapes or lu.decisions or lu.pros):
            raise TableurIllisibleException(
                "Aucun onglet reconnu : il faut au moins « Suivi des Tâches », les décisions ou le panel des prestataires."
            )
        source = re.sub(r"\.xlsx$", "", nom_fichier or "tableau", flags=re.IGNORECASE).strip() or "tableau"
        warnings = list(lu.avertissements)
        lignes: List[LigneImport] = []

        taches = LigneImport("tâches (salle de projet)")
        prevues = set()
        for t in lu.taches:
            if t.ref in prevues:
                warnings.append(f"Tâche n°{t.numero} en double dans le tableau : seule la première est reprise.")
                continue
            prevues.add(t.ref)
            if await self._taches.find_by_ref(t.ref):
                taches.deja_la += 1
                continue
            taches.nouveaux += 1
            if not apercu:
                await self._create_tache(
                    actor,
                    NouvelleTache(
                        title=t.title, description=t.description, status=t.status, pole=t.pole, due_date=t.due_date,
                        priority=t.priority, source="tableau", ref_externe=t.ref,
                    ),
                    commit=False,
                    announce=False,
                )
        lignes.append(taches)

        etapes = LigneImport("sous-étapes des tâches")
        membres = [m for m in await self._membres.find_all() if m.active]
        vues = set()
        for e in lu.etapes:
            if e.ref in vues:
                warnings.append(f"Étape « {e.title} » en double dans le tableau : reprise une seule fois.")
                continue
            vues.add(e.ref)
            if await self._etapes.find_by_ref(e.ref):
                etapes.deja_la += 1
                continue
            if e.parent_ref not in prevues and await self._taches.find_by_ref(e.parent_ref) is None:
                warnings.append(f"Étape « {e.title} » : sa tâche n°{e.parent_ref.rsplit(':', 1)[-1]} est introuvable, étape laissée de côté.")
                continue
            etapes.nouveaux += 1
            if not apercu:
                parent = await self._taches.find_by_ref(e.parent_ref)
                responsable = self._trouver(membres, e.responsable)
                notes = e.notes
                if e.responsable and responsable is None:
                    notes = f"Responsable indiqué dans le tableau : {e.responsable}\n{notes}".strip()
                await self._add_etape(
                    actor,
                    parent.id,
                    NouvelleEtape(
                        title=e.title, responsable_id=responsable.id if responsable else None, livrable=e.livrable,
                        status=e.status, start_date=e.start_date, due_date=e.due_date, notes=notes, ref_externe=e.ref,
                    ),
                    commit=False,
                )
        lignes.append(etapes)

        decisions = LigneImport("sujets de la salle du conseil")
        for d in lu.decisions:
            if d.ref in vues:
                warnings.append(f"Sujet « {d.titre} » en double dans le tableau : repris une seule fois.")
                continue
            vues.add(d.ref)
            if await self._decisions.find_by_ref(d.ref):
                decisions.deja_la += 1
                continue
            decisions.nouveaux += 1
            if not apercu:
                await self._create_decision(
                    actor,
                    NouvelleDecision(
                        titre=d.titre, demande=d.demande, decision=d.decision, objectif=d.objectif, liens=d.liens,
                        pole_concerne=d.pole_concerne, poles_en_charge=d.poles_en_charge, statut=d.statut,
                        date_demande=d.date_demande, ref_externe=d.ref,
                    ),
                    commit=False,
                    announce=False,
                )
        lignes.append(decisions)

        pros = LigneImport("fiches du panel des pros")
        for p in lu.pros:
            if p.ref in vues:
                warnings.append(f"Pro « {p.nom} » en double dans le tableau : reprise une seule fois.")
                continue
            vues.add(p.ref)
            if await self._pros.find_by_ref(p.ref):
                pros.deja_la += 1
                continue
            try:
                if not apercu:
                    await self._create_pro(
                        actor,
                        NouveauPro(
                            nom=p.nom, categorie=p.categorie, enseigne=p.enseigne, audience=p.audience, telephone=p.telephone,
                            email=p.email, contrat=p.contrat, acces_test=p.acces_test, numero=p.numero, ref_externe=p.ref,
                        ),
                        commit=False,
                        announce=False,
                    )
                pros.nouveaux += 1
            except BusinessException as exc:
                warnings.append(f"Pro « {p.nom} » non repris : {exc.message}")
        lignes.append(pros)

        documents = LigneImport("documents de la bibliothèque")
        for onglet in lu.autres:
            title = f"Tableau — {onglet.nom}"
            if await self._documents.find_by_title(title):
                documents.deja_la += 1
                continue
            documents.nouveaux += 1
            contenu, erreurs = en_markdown(onglet, source, today)
            if erreurs:
                warnings.append(f"Onglet « {onglet.nom} » : des cellules sont en erreur dans le tableau (#REF!, #ERROR!…).")
            if not apercu:
                category = "finances" if any(k in norm(onglet.nom) for k in _FINANCES) else "autre"
                document = await self._documents.save(
                    Document(title=title, category=category, content=contenu, created_by=actor.id, updated_by=actor.id)
                )
                await self._documents.add_version(
                    DocumentVersion(
                        document_id=document.id, version=1, title=title, category=category, content=contenu, author_id=actor.id,
                    )
                )
        lignes.append(documents)

        rapport = RapportImport(apercu=apercu, lignes=lignes, onglets=lu.onglets, avertissements=warnings)
        if not apercu and rapport.total_nouveaux:
            resume = ", ".join(
                part for part in (
                    _pluriel(taches.nouveaux, "tâche") if taches.nouveaux else "",
                    _pluriel(etapes.nouveaux, "étape") if etapes.nouveaux else "",
                    f"{_pluriel(decisions.nouveaux, 'sujet')} au conseil" if decisions.nouveaux else "",
                    f"{_pluriel(pros.nouveaux, 'pro')} au panel" if pros.nouveaux else "",
                    _pluriel(documents.nouveaux, "document") if documents.nouveaux else "",
                ) if part
            )
            await self._evenements.add(
                Evenement(actor_id=actor.id, verb="import_tableau", text=f"a repris le tableau « {source} » : {resume}.", link="/projet")
            )
        if not apercu:
            await self._transaction.commit()
        return rapport

    @staticmethod
    def _trouver(membres: List[Membre], nom: str) -> Optional[Membre]:
        """« Sullyvan » ou « Sullyvan Koffi » → le membre, s'il n'y a pas d'ambiguïté."""
        cible = norm(nom)
        if not cible:
            return None
        exact = [m for m in membres if norm(m.name) == cible]
        if len(exact) == 1:
            return exact[0]
        prenom = [m for m in membres if norm(m.name).split(" ")[0] == cible]
        return prenom[0] if len(prenom) == 1 else None
