"""Membres de départ. Liste des heads provisoire (à confirmer par Mohamed)."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import Channel, Member

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
