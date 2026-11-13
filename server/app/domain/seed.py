"""Membres de départ : équipe donnée par Mohamed le 13/11/2026."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import Channel, Member, Position, PositionHolder

TEAM = [
    dict(id="mohamed", name="Mohamed", kind="human", title="Gérant et directeur général", is_head=True,
         role="Fixer le cap, trouver l'argent, trancher, signer."),
    dict(id="marie-sophie", name="Marie-Sophie Aka", kind="human", title="Coordinatrice générale", is_head=True,
         role="Faire avancer les projets de toute l'entreprise, à l'heure et au budget."),
    dict(id="abraham", name="Abraham Doumbia", kind="human", title="Responsable Croissance", is_head=True,
         role="Faire grandir le nombre de salons actifs et de clientes qui réservent."),
    dict(id="sullyvan", name="Sullyvan Koffi", kind="human", title="Responsable Opérations et juridique", is_head=True,
         role="Faire tourner NYUMAN de façon fiable et légale : paiements, contrats, conformité."),
    dict(id="carmel", name="Carmel Didi", kind="human", title="Responsable Finance", is_head=True,
         role="Tenir l'argent juste et visible : trésorerie, marge, comptabilité."),
    dict(id="kevin", name="Kevin Diakité", kind="human", title="Responsable Produit et technique", is_head=True,
         role="Décider ce que l'app fait, et garantir qu'elle marche."),
    dict(id="kodjo", name="Kodjo", kind="agent", title="Produit et tech",
         role="App, serveur, back-office, builds. Seul à toucher au code de l'app."),
    dict(id="adjoua", name="Adjoua", kind="agent", title="Finance",
         role="Frais, prix, acomptes, projections, trésorerie."),
    dict(id="koffi", name="Koffi", kind="agent", title="Contradicteur",
         role="Relit chaque décision importante, dit non avec chiffres et alternative."),
    # Renommée Maeve par Mohamed le 13/11 ; l'identifiant reste "mariam" pour garder tout son historique.
    dict(id="mariam", name="Maeve", kind="agent", title="Chef de cabinet",
         role="Point du lundi, décisions en attente, lien avec la direction."),
    dict(id="kwame", name="Kwame", kind="agent", title="Construction de HQ",
         role="Construit Nyuman HQ, le QG de l'équipe."),
    # Ajoutés le 13/11 à la demande de Mohamed : un agent pour chaque responsable qui n'en avait pas.
    dict(id="aminata", name="Aminata", kind="agent", title="Croissance et lancement",
         role="Messages aux salons, contenus, suivi de chaque salon jusqu'à sa 1re réservation, lancement du 12/12."),
    dict(id="yao", name="Yao", kind="agent", title="Opérations et juridique",
         role="Contrats (Jèko, FeexPay, salons), litiges, réponses au support, conformité."),
]


async def seed(session: AsyncSession) -> None:
    existing = {m.id: m for m in (await session.scalars(select(Member))).all()}
    for m in TEAM:
        row = existing.get(m["id"])
        if row is None:
            session.add(Member(**m))
        else:  # noms et postes tenus à jour (le reste de la fiche appartient à la personne)
            row.name, row.title, row.is_head = m["name"], m["title"], m.get("is_head", False)
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
# Placements validés par Mohamed le 13/11 (équipe donnée le même jour).
# Appuis ajoutés après coup (13/11) : posés une fois s'ils manquent.
LATER_SUPPORT = [(3, "aminata"), (7, "yao")]
HOLDERS = [(1, "mohamed"), (2, "marie-sophie"), (3, "abraham"), (7, "sullyvan"), (9, "carmel"), (10, "kevin")]


async def seed_org(session: AsyncSession) -> None:
    if await session.get(Position, 1) is None:
        for pid, title, dept, parent, mission, hours in POSITIONS:
            session.add(Position(id=pid, title=title, department=dept, reports_to=parent, mission=mission, hours=hours))
        await session.flush()
        for pid, mid in AGENT_SUPPORT:
            session.add(PositionHolder(position_id=pid, member_id=mid, kind="support"))
        await session.commit()
    # Placements validés : ajoutés s'ils manquent (sans toucher aux autres choix faits dans HQ).
    links = {(l.position_id, l.member_id) for l in (await session.scalars(select(PositionHolder))).all()}
    for pid, mid in HOLDERS:
        if (pid, mid) not in links and await session.get(Member, mid) is not None:
            session.add(PositionHolder(position_id=pid, member_id=mid, kind="holder"))
    for pid, mid in LATER_SUPPORT:
        if (pid, mid) not in links and await session.get(Member, mid) is not None:
            session.add(PositionHolder(position_id=pid, member_id=mid, kind="support"))
    await session.commit()
