import importlib
import pkgutil
from pathlib import Path
from typing import Tuple

from fastapi import APIRouter, Depends, FastAPI

from core.session.session_middleware import get_current_membre

_CORE = Path(__file__).resolve().parent.parent / "adapters" / "core"


def public(func):
    """Marque une route accessible sans être connecté (ex. : la connexion elle-même)."""
    func._is_public = True
    return func


def _split(router: APIRouter) -> Tuple[APIRouter, APIRouter]:
    # Chaque route garde son chemin complet ; on la range côté public ou côté protégé.
    public_routes, protected_routes = APIRouter(), APIRouter()
    for route in router.routes:
        endpoint = getattr(route, "endpoint", None)
        target = public_routes if getattr(endpoint, "_is_public", False) else protected_routes
        target.routes.append(route)
    return public_routes, protected_routes


def discover_and_include_routers(app: FastAPI) -> None:
    """Inclut chaque `*_router` de adapters/core/<feature>/controller/*_controller.py.

    Comme dans nyuman-api : toute route exige une session, sauf celles marquées @public.
    """
    for feature in sorted(p.name for p in _CORE.iterdir() if (p / "controller").is_dir()):
        for module_info in pkgutil.iter_modules([str(_CORE / feature / "controller")]):
            if not module_info.name.endswith("_controller"):
                continue
            module = importlib.import_module(f"adapters.core.{feature}.controller.{module_info.name}")
            for name in dir(module):
                router = getattr(module, name)
                if name.endswith("_router") and isinstance(router, APIRouter):
                    public_routes, protected_routes = _split(router)
                    app.include_router(public_routes)
                    app.include_router(protected_routes, dependencies=[Depends(get_current_membre)])
