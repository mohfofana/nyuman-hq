import logging
from pathlib import Path
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from adapters.core.document.repository.document_repository import DocumentRepository
from adapters.core.membre.repository.membre_repository import MembreRepository
from domain.entities.document import Document, DocumentVersion
from domain.entities.membre import AGENT, COULEURS_HUMAINS, HEAD, HUMAIN, MEMBRE, Membre, initiales, nom_depuis_email

logger = logging.getLogger("hq")

OBJECTIFS_TITLE = "Objectifs Nyuman"
OBJECTIFS_PATH = Path(__file__).resolve().parent.parent / "seed" / "objectifs-nyuman.md"

# Les trois premiers agents. Ils sont membres de l'équipe dès le premier jour, et commencent à travailler en semaine 3.
AGENTS = [
    {"name": "Chef de cabinet", "initials": "CC", "color": "bleu", "title": "Point du lundi, ordre du jour", "pole": "direction"},
    {"name": "Contradicteur", "initials": "CT", "color": "rouge", "title": "Relit chaque proposition importante", "pole": ""},
    {"name": "Prospection", "initials": "PR", "color": "vert", "title": "Salons et barbiers à faire entrer", "pole": "operations"},
]


async def seed(session: AsyncSession, heads_initiaux: List[str]) -> None:
    """Idempotent : peut tourner à chaque démarrage sans rien dupliquer ni écraser ce que l'équipe a changé."""
    membres = MembreRepository(session)
    existing = await membres.find_all()

    agents = {m.name: m for m in existing if m.kind == AGENT}
    for agent in AGENTS:
        current = agents.get(agent["name"])
        if current is None:
            await membres.save(Membre(kind=AGENT, role=MEMBRE, status="en_preparation", **agent))
        elif not current.pole and agent["pole"]:
            # Agents créés avant l'arrivée des pôles : on les range dans leur pôle par défaut, une seule fois.
            current.pole = agent["pole"]
            current.title = agent["title"]
            await membres.save(current)

    # Les premiers comptes avaient l'adresse comme nom : on leur donne un nom lisible, en attendant le nom Google.
    for m in existing:
        if m.kind == HUMAIN and m.email and m.name == m.email:
            m.name = nom_depuis_email(m.email)
            m.initials = initiales(m.name)
            await membres.save(m)

    humans = sum(1 for m in existing if m.kind == HUMAIN)
    for email in heads_initiaux:
        if await membres.find_by_email(email) is None:
            await membres.save(
                Membre(
                    name=nom_depuis_email(email),
                    email=email,
                    kind=HUMAIN,
                    role=HEAD,
                    color=COULEURS_HUMAINS[humans % len(COULEURS_HUMAINS)],
                )
            )
            humans += 1
            logger.info("Head initial ajouté : %s", email)

    await _seed_objectifs(session, membres)
    await session.commit()


async def _seed_objectifs(session: AsyncSession, membres: MembreRepository) -> None:
    documents = DocumentRepository(session)
    if await documents.find_by_title(OBJECTIFS_TITLE) is not None:
        return
    heads = [m for m in await membres.find_all() if m.is_head]
    if not heads:
        return  # Le document sera déposé au démarrage suivant, quand un head existera.
    author = heads[0]
    content = OBJECTIFS_PATH.read_text(encoding="utf-8")
    document = await documents.save(
        Document(title=OBJECTIFS_TITLE, category="cerveau", content=content, created_by=author.id, updated_by=author.id)
    )
    await documents.add_version(
        DocumentVersion(
            document_id=document.id, version=1, title=document.title, category=document.category,
            content=document.content, author_id=author.id,
        )
    )
