from typing import Dict, List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.common.providers import get_tableur_reader
from adapters.core.import_tableau.import_tableau_app_config import ImportTableauAppConfig
from core.database import get_async_session
from core.session.session_middleware import get_current_membre
from domain.entities.membre import Membre
from use_cases.common.ports.out.tableur_reader import TableurReader

MAX_FICHIER = 5 * 1024 * 1024

import_router = APIRouter(prefix="/api/import", tags=["Reprise du tableau"])


class LigneImportViewModel(BaseModel):
    contenu: str
    nouveaux: int
    deja_la: int


class RapportImportViewModel(BaseModel):
    apercu: bool
    lignes: List[LigneImportViewModel]
    onglets: Dict[str, str]
    avertissements: List[str]


@import_router.post("/tableau", response_model=RapportImportViewModel)
async def import_tableau(
    fichier: UploadFile = File(...),
    apercu: bool = True,
    actor: Membre = Depends(get_current_membre),
    session: AsyncSession = Depends(get_async_session),
    reader: TableurReader = Depends(get_tableur_reader),
) -> RapportImportViewModel:
    """Par défaut, un aperçu (rien n'est écrit). Avec `apercu=false`, l'import est fait pour de bon."""
    if not (fichier.filename or "").lower().endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Envoie le tableau au format Excel (.xlsx) : Fichier → Télécharger → Microsoft Excel.")
    content = await fichier.read(MAX_FICHIER + 1)  # on ne lit jamais plus que la limite
    if len(content) > MAX_FICHIER:
        raise HTTPException(status_code=400, detail="Ce fichier dépasse 5 Mo.")
    rapport = await ImportTableauAppConfig(session, reader).import_tableau_use_case()(actor, content, fichier.filename or "", apercu)
    return RapportImportViewModel(
        apercu=rapport.apercu,
        lignes=[LigneImportViewModel(contenu=l.contenu, nouveaux=l.nouveaux, deja_la=l.deja_la) for l in rapport.lignes],
        onglets=rapport.onglets,
        avertissements=rapport.avertissements,
    )
