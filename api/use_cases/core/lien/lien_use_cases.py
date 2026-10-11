import html
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from domain.entities.evenement import Evenement
from domain.entities.lien_connexion import LienConnexion, hash_jeton
from domain.entities.membre import HUMAIN, Membre
from use_cases.common.ports.out.transaction import Transaction
from use_cases.core.evenement.repository.evenement_repository import EvenementRepository
from use_cases.core.lien.exceptions.lien_exceptions import LienInvalideException
from use_cases.core.lien.repository.lien_repository import LienRepository
from use_cases.core.membre.exceptions.membre_exceptions import AccesRefuseException
from use_cases.core.membre.repository.membre_repository import MembreRepository

MAX_LIENS = 3  # liens demandés au plus par personne…
FENETRE = timedelta(minutes=15)  # …sur ce laps de temps


@dataclass(frozen=True)
class EmailLien:
    to: str
    subject: str
    text: str
    html: str


class DemanderLienUseCase:
    """Prépare un lien de connexion pour une adresse de la maison.

    Renvoie None, sans rien dire de plus, si l'adresse n'a pas accès ou a déjà demandé trop de liens :
    la réponse est la même dans tous les cas, pour qu'on ne puisse pas deviner qui a un compte.
    """

    def __init__(
        self,
        membre_repository: MembreRepository,
        lien_repository: LienRepository,
        transaction: Transaction,
        public_url: str,
        minutes: int,
    ):
        self._membre_repository = membre_repository
        self._lien_repository = lien_repository
        self._transaction = transaction
        self._public_url = public_url.rstrip("/")
        self._minutes = minutes

    async def __call__(self, email: str) -> Optional[EmailLien]:
        membre = await self._membre_repository.find_by_email(email.strip().lower())
        if membre is None or membre.kind != HUMAIN or not membre.active or not membre.email:
            return None

        now = datetime.now(timezone.utc)
        await self._lien_repository.purger(now - timedelta(days=1))
        if await self._lien_repository.count_since(membre.id, now - FENETRE) >= MAX_LIENS:
            await self._transaction.commit()
            return None

        jeton = secrets.token_urlsafe(32)
        await self._lien_repository.add(
            LienConnexion(
                membre_id=membre.id,
                token_hash=hash_jeton(jeton),
                expires_at=now + timedelta(minutes=self._minutes),
                created_at=now,
            )
        )
        await self._transaction.commit()
        # Le jeton est après « # » : le navigateur ne l'envoie jamais à un serveur, il n'apparaît dans aucun journal.
        return self._email(membre, f"{self._public_url}/connexion#jeton={jeton}")

    def _email(self, membre: Membre, lien: str) -> EmailLien:
        prenom = (membre.name or "").split(" ")[0] or "toi"
        texte = (
            f"Bonjour {prenom},\n\n"
            f"Voici ton lien pour entrer dans Nyuman HQ. Il marche une seule fois, pendant {self._minutes} minutes :\n\n"
            f"{lien}\n\n"
            "Si tu n'as rien demandé, ignore ce message : personne ne peut entrer sans ce lien.\n\n"
            "Nyuman HQ"
        )
        p, href = html.escape(prenom), html.escape(lien, quote=True)
        page = f"""<!doctype html>
<html lang="fr"><body style="margin:0;background:#f6f0e7;font-family:Arial,Helvetica,sans-serif;color:#1e130c">
  <div style="max-width:480px;margin:0 auto;padding:32px 20px">
    <p style="font-size:13px;letter-spacing:.08em;text-transform:uppercase;color:#9c4f0a;margin:0 0 20px">Nyuman HQ</p>
    <p style="font-size:17px;margin:0 0 12px">Bonjour {p},</p>
    <p style="font-size:15px;line-height:1.5;margin:0 0 24px">Voici ton lien pour entrer dans la maison.
      Il marche une seule fois, pendant {self._minutes} minutes.</p>
    <p style="margin:0 0 28px"><a href="{href}" style="display:inline-block;background:#bc600d;color:#ffffff;
      text-decoration:none;font-weight:bold;padding:13px 22px;border-radius:10px">Entrer dans HQ</a></p>
    <p style="font-size:13px;line-height:1.5;color:#6b5a4c;margin:0">Si tu n'as rien demandé, ignore ce message :
      personne ne peut entrer sans ce lien.</p>
  </div>
</body></html>"""
        return EmailLien(to=membre.email, subject="Ton lien pour entrer dans Nyuman HQ", text=texte, html=page)


class ValiderLienUseCase:
    """Ouvre la session si le lien est bon, pas expiré et pas encore utilisé. Les autres liens en attente sont annulés."""

    def __init__(
        self,
        membre_repository: MembreRepository,
        lien_repository: LienRepository,
        evenement_repository: EvenementRepository,
        transaction: Transaction,
    ):
        self._membre_repository = membre_repository
        self._lien_repository = lien_repository
        self._evenement_repository = evenement_repository
        self._transaction = transaction

    async def __call__(self, jeton: str) -> Membre:
        now = datetime.now(timezone.utc)
        lien = await self._lien_repository.find_by_hash(hash_jeton(jeton.strip()))
        if lien is None or not lien.utilisable(now) or not await self._lien_repository.consommer(lien.id, now):
            raise LienInvalideException()

        membre = await self._membre_repository.find_by_id(lien.membre_id)
        if membre is None or membre.kind != HUMAIN or not membre.active:
            await self._transaction.commit()
            raise AccesRefuseException()

        await self._lien_repository.annuler_restants(membre.id, now)
        first_visit = membre.last_seen_at is None
        membre.last_seen_at = now
        membre = await self._membre_repository.save(membre)
        if first_visit:
            await self._evenement_repository.add(
                Evenement(actor_id=membre.id, verb="arrivee", text="est entré dans la maison pour la première fois.")
            )
        await self._transaction.commit()
        return membre
