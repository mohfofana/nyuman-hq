from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Optional

from domain.entities.evenement import Evenement
from domain.entities.membre import HUMAIN, POLES, Membre
from domain.entities.objectif import METRIC_MANUEL, Objectif
from domain.value_objects.kpi import KPI_KEYS
from use_cases.common.ports.out.transaction import Transaction
from use_cases.core.evenement.repository.evenement_repository import EvenementRepository
from use_cases.core.membre.exceptions.membre_exceptions import ReserveAuxHeadsException
from use_cases.core.objectif.exceptions.objectif_exceptions import ObjectifInvalideException
from use_cases.core.objectif.repository.objectif_repository import ObjectifRepository


@dataclass
class ObjectifInput:
    title: str
    quarter: str
    metric: str
    target: float
    start_date: date
    end_date: date
    current_manual: Optional[float] = None  # point de départ d'un chiffre suivi à la main


def _texte_evenement(objectif: Objectif) -> str:
    if objectif.pole:
        return f"a fixé l’objectif du pôle {POLES[objectif.pole]} : « {objectif.title} »."
    return f"a fixé l’objectif du trimestre : « {objectif.title} »."


def _lien(objectif: Objectif) -> str:
    return "/bureaux" if objectif.pole else "/"


class SaveCurrentObjectifUseCase:
    """Un head fixe l'objectif du trimestre, pour toute la maison ou pour un pôle.

    S'il est encore en cours, on le corrige ; sinon on en crée un nouveau.
    """

    def __init__(
        self,
        objectif_repository: ObjectifRepository,
        evenement_repository: EvenementRepository,
        transaction: Transaction,
    ):
        self._objectif_repository = objectif_repository
        self._evenement_repository = evenement_repository
        self._transaction = transaction

    async def __call__(self, actor: Membre, data: ObjectifInput, today: date, pole: str = "") -> Objectif:
        if not actor.is_head:
            raise ReserveAuxHeadsException()
        if pole and pole not in POLES:
            raise ObjectifInvalideException("Ce pôle n’existe pas.")
        if not data.title.strip() or not data.quarter.strip():
            raise ObjectifInvalideException("L’objectif a besoin d’une phrase et d’un trimestre.")
        if data.metric not in KPI_KEYS and data.metric != METRIC_MANUEL:
            raise ObjectifInvalideException("Ce chiffre n’est pas suivi par HQ.")
        if data.target <= 0:
            raise ObjectifInvalideException("La cible doit être plus grande que zéro.")
        if data.end_date <= data.start_date:
            raise ObjectifInvalideException("La fin doit venir après le début.")

        objectif = await self._objectif_repository.find_latest(pole)
        if objectif is not None and objectif.end_date >= today:
            objectif.title = data.title.strip()
            objectif.quarter = data.quarter.strip()
            objectif.metric = data.metric
            objectif.target = data.target
            objectif.start_date = data.start_date
            objectif.end_date = data.end_date
            if data.metric == METRIC_MANUEL and data.current_manual is not None:
                objectif.current_manual = data.current_manual
            objectif.updated_at = datetime.now(timezone.utc)
        else:
            objectif = Objectif(
                title=data.title.strip(),
                quarter=data.quarter.strip(),
                metric=data.metric,
                target=data.target,
                start_date=data.start_date,
                end_date=data.end_date,
                pole=pole,
                current_manual=(data.current_manual or 0.0) if data.metric == METRIC_MANUEL else None,
                created_by=actor.id,
            )
        objectif = await self._objectif_repository.save(objectif)
        await self._evenement_repository.add(
            Evenement(actor_id=actor.id, verb="objectif_fixe", text=_texte_evenement(objectif), link=_lien(objectif))
        )
        await self._transaction.commit()
        return objectif


class UpdateAvancementUseCase:
    """Met à jour un chiffre suivi à la main : un head, ou un membre du pôle concerné."""

    def __init__(
        self,
        objectif_repository: ObjectifRepository,
        evenement_repository: EvenementRepository,
        transaction: Transaction,
    ):
        self._objectif_repository = objectif_repository
        self._evenement_repository = evenement_repository
        self._transaction = transaction

    async def __call__(self, actor: Membre, objectif_id: int, value: float) -> Objectif:
        objectif = await self._objectif_repository.find_by_id(objectif_id)
        if objectif is None:
            raise ObjectifInvalideException("Cet objectif n’existe pas.")
        if not objectif.is_manual:
            raise ObjectifInvalideException("Ce chiffre vient de l’app : il se met à jour tout seul.")
        if not (actor.is_head or (actor.kind == HUMAIN and objectif.pole and actor.pole == objectif.pole)):
            raise ReserveAuxHeadsException()
        if value < 0:
            raise ObjectifInvalideException("Le chiffre ne peut pas être négatif.")
        objectif.current_manual = value
        objectif.updated_at = datetime.now(timezone.utc)
        objectif = await self._objectif_repository.save(objectif)
        label = POLES.get(objectif.pole, "la maison")
        await self._evenement_repository.add(
            Evenement(
                actor_id=actor.id,
                verb="objectif_avance",
                text=f"a mis à jour l’objectif {('du pôle ' + label) if objectif.pole else 'du trimestre'} : {value:g} sur {objectif.target:g}.",
                link=_lien(objectif),
            )
        )
        await self._transaction.commit()
        return objectif
