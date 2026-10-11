from datetime import datetime, timezone
from typing import Dict, List, Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.common.providers import get_capture_storage, get_testflight_gateway
from adapters.core.membre.repository.membre_repository import MembreRepository
from adapters.core.retour.contract.retour_view_model import ConvertRetourRequest, RetoursEtatViewModel, RetourViewModel
from adapters.core.retour.retour_app_config import RetourAppConfig, TestflightState
from adapters.core.tache.contract.tache_view_model import TacheViewModel
from core.database import get_async_session
from core.session.session_middleware import get_current_membre
from domain.entities.membre import Membre
from domain.entities.retour import NOUVEAU
from use_cases.common.ports.out.testflight_gateway import CaptureStorage, TestflightGateway
from use_cases.core.retour.retour_use_cases import MAX_CAPTURE_BYTES, MAX_CAPTURES, NouveauRetour

retour_router = APIRouter(prefix="/api/retours", tags=["Retours des testeurs"])

_MEDIA = {"png": "image/png", "jpg": "image/jpeg", "webp": "image/webp", "heic": "image/heic", "heif": "image/heif"}


class RetourController:
    def __init__(self, session: AsyncSession, storage: CaptureStorage, gateway: TestflightGateway):
        self.config = RetourAppConfig(session, storage, gateway)
        self._membres = MembreRepository(session)

    async def membres(self) -> Dict[int, Membre]:
        return {m.id: m for m in await self._membres.find_all()}


def retour_controller(
    session: AsyncSession = Depends(get_async_session),
    storage: CaptureStorage = Depends(get_capture_storage),
    gateway: TestflightGateway = Depends(get_testflight_gateway),
) -> RetourController:
    return RetourController(session, storage, gateway)


@retour_router.get("", response_model=List[RetourViewModel])
async def list_retours(
    statut: Literal["nouveau", "en_tache", "classe", "tous"] = Query(default="nouveau"),
    controller: RetourController = Depends(retour_controller),
) -> List[RetourViewModel]:
    retours = await controller.config.get_retour_list_use_case()(None if statut == "tous" else statut)
    membres = await controller.membres()
    return [RetourViewModel.of(r, membres) for r in retours]


@retour_router.post("", response_model=RetourViewModel, status_code=201)
async def create_retour(
    kind: Literal["bug", "idee", "remarque"] = Form(...),
    comment: str = Form(default="", max_length=5000),
    espace: Literal["cliente", "pro", ""] = Form(default=""),
    device_model: str = Form(default="", max_length=80),
    os_version: str = Form(default="", max_length=40),
    build_version: str = Form(default="", max_length=40),
    captures: List[UploadFile] = File(default=[]),
    actor: Membre = Depends(get_current_membre),
    controller: RetourController = Depends(retour_controller),
) -> RetourViewModel:
    if len(captures) > MAX_CAPTURES:
        raise HTTPException(status_code=400, detail=f"{MAX_CAPTURES} captures au maximum par retour.")
    files = []
    for upload in captures:
        content = await upload.read(MAX_CAPTURE_BYTES + 1)  # on ne lit jamais plus que la limite
        files.append((content, (upload.content_type or "").lower()))
    retour = await controller.config.create_retour_use_case()(
        actor,
        NouveauRetour(
            kind=kind, comment=comment, espace=espace, device_model=device_model,
            os_version=os_version, build_version=build_version, captures=files,
        ),
    )
    return RetourViewModel.of(retour, await controller.membres())


@retour_router.get("/etat", response_model=RetoursEtatViewModel)
async def etat(controller: RetourController = Depends(retour_controller)) -> RetoursEtatViewModel:
    return RetoursEtatViewModel(
        nouveaux=await controller.config.retour_repository.count(NOUVEAU),
        testflight_branche=controller.config.gateway.configured,
        derniere_synchro=TestflightState.derniere_synchro,
        derniere_erreur=TestflightState.derniere_erreur,
    )


@retour_router.post("/synchroniser")
async def synchroniser(controller: RetourController = Depends(retour_controller)) -> Dict[str, int]:
    nouveaux = await controller.config.sync_retours_use_case()()
    TestflightState.derniere_synchro = datetime.now(timezone.utc)
    TestflightState.derniere_erreur = None
    return {"nouveaux": nouveaux}


@retour_router.get("/{retour_id}/captures/{index}")
async def capture(retour_id: int, index: int, controller: RetourController = Depends(retour_controller)) -> FileResponse:
    retour = await controller.config.get_retour_by_id_use_case()(retour_id)
    if index < 0 or index >= len(retour.captures):
        raise HTTPException(status_code=404, detail="Capture introuvable.")
    name = retour.captures[index]
    path = controller.config.storage.path(name)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Capture introuvable sur le serveur.")
    return FileResponse(path, media_type=_MEDIA.get(name.rsplit(".", 1)[-1], "application/octet-stream"),
                        headers={"Cache-Control": "private, max-age=86400"})


@retour_router.post("/{retour_id}/tache", response_model=TacheViewModel, status_code=201)
async def convert(
    retour_id: int,
    request: ConvertRetourRequest,
    actor: Membre = Depends(get_current_membre),
    controller: RetourController = Depends(retour_controller),
) -> TacheViewModel:
    tache = await controller.config.convert_retour_use_case()(actor, retour_id, request.title, request.assignee_id)
    return TacheViewModel.of(tache, await controller.membres())


@retour_router.post("/{retour_id}/classer", response_model=RetourViewModel)
async def classer(retour_id: int, controller: RetourController = Depends(retour_controller)) -> RetourViewModel:
    retour = await controller.config.classer_retour_use_case()(retour_id)
    return RetourViewModel.of(retour, await controller.membres())
