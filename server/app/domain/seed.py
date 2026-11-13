"""Membres de départ. Liste des heads provisoire (à confirmer par Mohamed)."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import Channel, Member, Position, PositionHolder

TEAM = [
    dict(id="mohamed", name="Mohamed", kind="human", title="Fondateur", is_head=True,
         role="Vision, décisions finales, relations partenaires."),
    dict(id="kevin", name="Kevin", kind="human", title="CTO", is_head=True,
         role="Technique : serveur, sécurité, mises en ligne, logique d'argent."),
    dict(id="sullyvan", name="Chris-Sullyvan Koffi", kind="human", is_head=True,
         title="Directeur opérationnel et administratif", role="Juridique, contrats, opérations."),
    dict(id="kodjo", name="Kodjo", kind="agent", title="Produit et tech",
         role="App, serveur, back-office, builds. Seul à toucher au code de l'app."),
    dict(id="adjoua", name="Adjoua", kind="agent", title="Finance",
         role="Frais, prix, acomptes, projections, trésorerie."),
    dict(id="koffi", name="Koffi", kind="agent", title="Contradicteur",
         role="Relit chaque décision importante, dit non avec chiffres et alternative."),
    dict(id="mariam", name="Mariam", kind="agent", title="Chef de cabinet",
         role="Point du lundi, décisions en attente, lien avec la direction."),
    dict(id="kwame", name="Kwame", kind="agent", title="Construction de HQ",
         role="Construit Nyuman HQ, le QG de l'équipe."),
]


async def seed(session: AsyncSession) -> None:
    existing = set((await session.scalars(select(Member.id))).all())
    for m in TEAM:
        if m["id"] not in existing:
            session.add(Member(**m))
    await session.commit()


CHANNELS = [
    dict(id="general", name="général", topic="Tout ce qui concerne toute l'équipe."),
    dict(id="tech", name="tech", topic="App, serveur, builds, bugs."),
    dict(id="finance", name="finance", topic="Frais, acomptes, trésorerie."),
    dict(id="operations", name="opérations", topic="Salons, partenaires, terrain."),
]


async def seed_channels(session: AsyncSession) -> None:
    existing = set((await session.scalars(select(Channel.id))).all())
    for c in CHANNELS:
        if c["id"] not in existing:
            session.add(Channel(kind="channel", created_by="mohamed", **c))
    await session.commit()


# Fiches de poste NYUMAN (doc « Fiches de poste NYUMAN », 12/11/2026). Postes sans nom : on y place les personnes ensuite.
POSITIONS = [
    (1, "Gérant et directeur général", "Direction générale", None, "Fixer le cap, trouver l'argent, trancher, signer", "12 à 15"),
    (2, "Coordinateur général", "Direction générale", 1, "Faire avancer les projets de toute l'entreprise, à l'heure et au budget", "10"),
    (3, "Responsable Croissance", "Croissance", 1, "Faire grandir le nombre de salons actifs et de clientes qui réservent", "15"),
    (4, "Chargé marketing et contenus", "Croissance", 3, "Faire connaître NYUMAN aux clientes et donner envie de réserver", "10"),
    (5, "Chargé influence et partenariats", "Croissance", 3, "Ouvrir les portes : personnalités, créateurs, lieux, marques", "5"),
    (6, "Chargé activation terrain", "Croissance", 3, "Amener chaque salon signé jusqu'à sa première réservation honorée", "12 à 15"),
    (7, "Responsable Opérations et juridique", "Opérations", 1, "Faire tourner NYUMAN de façon fiable et légale : paiements, contrats, conformité", "10"),
    (8, "Chargé relation prestataires et support", "Opérations", 7, "Garder les salons actifs et répondre à tout le monde, vite et juste", "10"),
    (9, "Responsable Finance", "Finance", 1, "Tenir l'argent juste et visible : trésorerie, marge, comptabilité", "5"),
    (10, "Responsable Produit et technique", "Produit et technique", 1, "Décider ce que l'app fait, et garantir qu'elle marche", "15"),
    (11, "Développeur mobile", "Produit et technique", 10, "Des apps iPhone et Android stables sur un téléphone d'entrée de gamme", "10 à 15"),
    (12, "Développeur serveur et web", "Produit et technique", 10, "Un serveur, des paiements et un site qui ne tombent pas", "10 à 15"),
]

# Appui des agents (proposition de Kwame) : un agent n'occupe jamais un poste, il appuie la personne qui le tient.
AGENT_SUPPORT = [(9, "adjoua"), (10, "kodjo"), (1, "koffi"), (2, "mariam"), (10, "kwame")]


async def seed_org(session: AsyncSession) -> None:
    if await session.get(Position, 1) is None:
        for pid, title, dept, parent, mission, hours in POSITIONS:
            session.add(Position(id=pid, title=title, department=dept, reports_to=parent, mission=mission, hours=hours))
        await session.flush()
        for pid, mid in AGENT_SUPPORT:
            session.add(PositionHolder(position_id=pid, member_id=mid, kind="support"))
        await session.commit()
