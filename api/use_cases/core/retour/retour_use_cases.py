import logging
import uuid
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from domain.entities.evenement import Evenement
from domain.entities.membre import Membre
from domain.entities.retour import (
    BUG,
    CLASSE,
    EN_TACHE,
    ESPACES,
    IDEE,
    KINDS,
    NOUVEAU,
    REMARQUE,
    SOURCE_TESTFLIGHT,
    Retour,
)
from use_cases.common.ports.out.testflight_gateway import CaptureStorage, TestflightGateway
from use_cases.common.ports.out.transaction import Transaction
from use_cases.core.evenement.repository.evenement_repository import EvenementRepository
from use_cases.core.retour.exceptions.retour_exceptions import (
    RetourInvalideException,
    RetourNotFoundException,
    TestflightNonBrancheException,
)
from use_cases.core.retour.repository.retour_repository import RetourRepository
from use_cases.core.tache.tache_use_cases import CreateTacheUseCase, NouvelleTache

logger = logging.getLogger("hq")

IMAGE_TYPES = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp", "image/heic": "heic", "image/heif": "heif"}
MAX_CAPTURES = 6
MAX_CAPTURE_BYTES = 8 * 1024 * 1024

_VERBES = {
    BUG: "a signalé un bug",
    IDEE: "a proposé une idée",
    REMARQUE: "a fait une remarque",
}


def _court(text: str, size: int = 90) -> str:
    text = " ".join(text.split())
    return text if len(text) <= size else text[:size].rsplit(" ", 1)[0] + "…"


@dataclass
class NouveauRetour:
    kind: str
    comment: str = ""
    espace: str = ""
    device_model: str = ""
    os_version: str = ""
    build_version: str = ""
    captures: List[Tuple[bytes, str]] = field(default_factory=list)  # (contenu, type)


class CreateRetourUseCase:
    """Un membre de l'équipe signale un bug, une idée ou une remarque, captures à l'appui (au lieu de WhatsApp)."""

    def __init__(
        self,
        retour_repository: RetourRepository,
        storage: CaptureStorage,
        evenement_repository: EvenementRepository,
        transaction: Transaction,
    ):
        self._retours = retour_repository
        self._storage = storage
        self._evenements = evenement_repository
        self._transaction = transaction

    async def __call__(self, actor: Membre, data: NouveauRetour) -> Retour:
        if data.kind not in KINDS:
            raise RetourInvalideException("Choisis : bug, idée ou remarque.")
        if data.espace not in ESPACES:
            raise RetourInvalideException("Côté de l’app inconnu.")
        comment = data.comment.strip()
        if not comment and not data.captures:
            raise RetourInvalideException("Écris ce qui se passe ou ajoute au moins une capture.")
        if len(data.captures) > MAX_CAPTURES:
            raise RetourInvalideException(f"{MAX_CAPTURES} captures au maximum par retour.")
        for content, content_type in data.captures:
            if content_type not in IMAGE_TYPES:
                raise RetourInvalideException("Seules les images sont acceptées (PNG, JPEG, WebP, HEIC).")
            if len(content) > MAX_CAPTURE_BYTES:
                raise RetourInvalideException("Une capture dépasse 8 Mo.")

        prefix = uuid.uuid4().hex[:12]
        captures = [
            self._storage.save(f"hq-{prefix}-{i}.{IMAGE_TYPES[content_type]}", content)
            for i, (content, content_type) in enumerate(data.captures)
        ]
        retour = await self._retours.save(
            Retour(
                kind=data.kind,
                comment=comment,
                author_id=actor.id,
                espace=data.espace,
                device_model=data.device_model.strip()[:80],
                os_version=data.os_version.strip()[:40],
                build_version=data.build_version.strip()[:40],
                captures=captures,
            )
        )
        resume = f" : « {_court(comment)} »" if comment else " (avec capture)"
        await self._evenements.add(
            Evenement(actor_id=actor.id, verb=f"retour_{data.kind}", text=f"{_VERBES[data.kind]}{resume}.", link=f"/projet?retour={retour.id}")
        )
        await self._transaction.commit()
        return retour


class SyncRetoursUseCase:
    """Import TestFlight (testeurs externes, plus tard) : range les nouveaux retours, ignore ceux déjà connus."""

    def __init__(
        self,
        gateway: TestflightGateway,
        retour_repository: RetourRepository,
        storage: CaptureStorage,
        transaction: Transaction,
    ):
        self._gateway = gateway
        self._retours = retour_repository
        self._storage = storage
        self._transaction = transaction

    async def __call__(self) -> int:
        if not self._gateway.configured:
            raise TestflightNonBrancheException()
        known = await self._retours.known_asc_ids()
        nouveaux = 0
        for source in await self._gateway.fetch():
            if source.asc_id in known:
                continue
            captures: List[str] = []
            for index, url in enumerate(source.screenshot_urls):
                try:
                    content, content_type = await self._gateway.download(url)
                    ext = IMAGE_TYPES.get(content_type.split(";")[0].strip(), "jpg")
                    captures.append(self._storage.save(f"tf-{source.asc_id}-{index}.{ext}", content))
                except Exception as exc:  # une capture manquante ne doit pas faire perdre le retour
                    logger.warning("Capture TestFlight %s non récupérée : %s", source.asc_id, exc)
            await self._retours.save(
                Retour(
                    kind=BUG if source.kind == "plantage" else REMARQUE,
                    source=SOURCE_TESTFLIGHT,
                    asc_id=source.asc_id,
                    created_at=source.created_at,
                    comment=source.comment,
                    tester_email=source.email,
                    device_model=source.device_model,
                    os_version=source.os_version,
                    build_version=source.build_version,
                    captures=captures,
                )
            )
            nouveaux += 1
        await self._transaction.commit()
        return nouveaux


class GetRetourListUseCase:
    def __init__(self, retour_repository: RetourRepository):
        self._retours = retour_repository

    async def __call__(self, statut: Optional[str] = NOUVEAU) -> List[Retour]:
        return await self._retours.search(statut)


class GetRetourByIdUseCase:
    def __init__(self, retour_repository: RetourRepository):
        self._retours = retour_repository

    async def __call__(self, retour_id: int) -> Retour:
        retour = await self._retours.find_by_id(retour_id)
        if retour is None:
            raise RetourNotFoundException()
        return retour


class ConvertRetourUseCase:
    """Transforme un retour en tâche de la salle de projet, avec tout le contexte utile pour la corriger."""

    def __init__(
        self,
        retour_repository: RetourRepository,
        create_tache: CreateTacheUseCase,
        evenement_repository: EvenementRepository,
        transaction: Transaction,
    ):
        self._retours = retour_repository
        self._create_tache = create_tache
        self._evenements = evenement_repository
        self._transaction = transaction

    async def __call__(self, actor: Membre, retour_id: int, title: Optional[str], assignee_id: Optional[int]):
        retour = await self._retours.find_by_id(retour_id)
        if retour is None:
            raise RetourNotFoundException()
        if retour.statut == EN_TACHE:
            raise RetourInvalideException("Ce retour est déjà devenu une tâche.")
        label = {BUG: "Bug", IDEE: "Idée", REMARQUE: "Remarque"}[retour.kind]
        default_title = f"{label} : {_court(retour.comment, 80)}" if retour.comment else f"{label} signalé avec capture"
        details = [f"> {retour.comment}" if retour.comment else "> (pas de commentaire, voir les captures)", ""]
        if retour.espace:
            details.append(f"- Côté de l’app : {'clientes' if retour.espace == 'cliente' else 'pros'}")
        if retour.device_model or retour.os_version:
            details.append(f"- Appareil : {retour.device_model or 'inconnu'}, iOS {retour.os_version or '?'}")
        if retour.build_version:
            details.append(f"- Build : {retour.build_version}")
        details.append(f"- Retour n° {retour.id}, envoyé le {retour.created_at:%d/%m/%Y à %H:%M}")
        if retour.tester_email:
            details.append(f"- Testeur TestFlight : {retour.tester_email}")

        tache = await self._create_tache(
            actor,
            NouvelleTache(
                title=(title or default_title).strip()[:200],
                description="\n".join(details),
                assignee_id=assignee_id,
                source="testflight" if retour.source == SOURCE_TESTFLIGHT else "humain",
                retour_id=retour.id,
            ),
            commit=False,
            announce=False,
        )
        retour.statut = EN_TACHE
        retour.tache_id = tache.id
        await self._retours.save(retour)
        await self._evenements.add(
            Evenement(
                actor_id=actor.id,
                verb="retour_en_tache",
                text=f"a transformé un retour en tâche : « {tache.title} ».",
                link=f"/projet?tache={tache.id}",
            )
        )
        await self._transaction.commit()
        return tache


class ClasserRetourUseCase:
    """Range un retour sans suite (doublon, déjà corrigé…). Il reste consultable, rien n'est effacé."""

    def __init__(self, retour_repository: RetourRepository, transaction: Transaction):
        self._retours = retour_repository
        self._transaction = transaction

    async def __call__(self, retour_id: int) -> Retour:
        retour = await self._retours.find_by_id(retour_id)
        if retour is None:
            raise RetourNotFoundException()
        retour.statut = CLASSE
        retour = await self._retours.save(retour)
        await self._transaction.commit()
        return retour
