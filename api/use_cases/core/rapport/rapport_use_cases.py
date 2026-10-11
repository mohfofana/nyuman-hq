from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import List

from core.exceptions import BusinessException, ErrorType
from domain.entities.evenement import Evenement
from domain.entities.membre import Membre
from domain.entities.rapport import Rapport, semaine_iso
from use_cases.common.ports.out.transaction import Transaction
from use_cases.core.evenement.repository.evenement_repository import EvenementRepository
from use_cases.core.rapport.repository.rapport_repository import RapportRepository

MAX_CHAMP = 4000


class RapportInvalideException(BusinessException):
    def __init__(self, message: str):
        super().__init__(message, ErrorType.VALIDATION_ERROR)


@dataclass
class ContenuRapport:
    fait: str = ""
    en_cours: str = ""
    bloque: str = ""
    propositions: str = ""


class PublishRapportUseCase:
    """Chacun publie son rapport de la semaine ; il peut le compléter tant que la semaine n'est pas finie."""

    def __init__(self, rapport_repository: RapportRepository, evenement_repository: EvenementRepository, transaction: Transaction):
        self._rapports = rapport_repository
        self._evenements = evenement_repository
        self._transaction = transaction

    async def __call__(self, actor: Membre, contenu: ContenuRapport, today: date) -> Rapport:
        champs = {k: v.strip() for k, v in vars(contenu).items()}
        if not any(champs.values()):
            raise RapportInvalideException("Le rapport est vide : écris au moins une ligne.")
        if any(len(v) > MAX_CHAMP for v in champs.values()):
            raise RapportInvalideException("Une partie du rapport est trop longue.")
        propositions = [l for l in champs["propositions"].splitlines() if l.strip()]
        if len(propositions) > 3:
            raise RapportInvalideException("3 propositions au maximum : garde les meilleures.")

        week = semaine_iso(today)
        rapport = await self._rapports.find_by_author_week(actor.id, week)
        first = rapport is None
        if first:
            rapport = Rapport(author_id=actor.id, week=week, pole=actor.pole)
        for key, value in champs.items():
            setattr(rapport, key, value)
        rapport.updated_at = datetime.now(timezone.utc)
        rapport = await self._rapports.save(rapport)
        if first:
            numero = int(week.split("W")[1])
            await self._evenements.add(
                Evenement(
                    actor_id=actor.id,
                    verb="rapport_publie",
                    text=f"a publié son rapport de la semaine {numero}.",
                    link=f"/bureaux/{actor.id}#rapport",
                )
            )
        await self._transaction.commit()
        return rapport


class GetRapportsUseCase:
    def __init__(self, rapport_repository: RapportRepository):
        self._rapports = rapport_repository

    async def by_author(self, author_id: int, limit: int = 8) -> List[Rapport]:
        return await self._rapports.list_by_author(author_id, min(limit, 52))

    async def by_week(self, today: date) -> List[Rapport]:
        return await self._rapports.list_by_week(semaine_iso(today))
