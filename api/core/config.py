import secrets
from functools import cached_property
from pathlib import Path
from typing import List, Literal, Optional

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

API_DIR = Path(__file__).resolve().parent.parent


def to_async_url(url: str) -> str:
    """Railway et Postgres donnent postgresql://… ; SQLAlchemy asynchrone attend postgresql+asyncpg://…"""
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+asyncpg://" + url[len(prefix):]
    return url


class Settings(BaseSettings):
    """Réglages de HQ, lus dans les variables d'environnement (ou le fichier api/.env)."""

    model_config = SettingsConfigDict(env_file=API_DIR / ".env", extra="ignore")

    ENVIRONMENT: Literal["development", "test", "production"] = "development"
    DATABASE_URL: str = f"sqlite+aiosqlite:///{(API_DIR / 'hq.db').as_posix()}"

    HQ_SESSION_SECRET: Optional[str] = None
    SESSION_DAYS: int = 7

    GOOGLE_CLIENT_ID: Optional[str] = None

    # Connexion par lien envoyé par email (les boîtes @nyuman.app sont chez Netim).
    # Le mot de passe de la boîte est entré par l'équipe dans les variables d'environnement du serveur.
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 465  # 465 = SSL, 587 = STARTTLS
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM: Optional[str] = None  # par défaut : SMTP_USER
    HQ_PUBLIC_URL: str = "http://localhost:5173"  # adresse de HQ, pour fabriquer le lien
    LIEN_MINUTES: int = 15
    HQ_DEV_LOGIN: bool = False
    HQ_HEADS_INITIAUX: str = ""
    HQ_ORIGINES: str = "http://localhost:5173,http://127.0.0.1:5173"

    # Chiffres de l'app : lecture seule de la base de nyuman-api (prioritaire), ou sa route statistiques.
    NYUMAN_DB_LECTURE_URL: Optional[str] = None
    NYUMAN_API_URL: Optional[str] = None
    NYUMAN_STATS_KEY: Optional[str] = None
    KPI_CACHE_SECONDES: int = 60

    HQ_WEB_DIR: str = "../web/dist"
    # Fichiers envoyés dans HQ (captures des retours). Sur le serveur : un volume Docker persistant.
    HQ_UPLOADS_DIR: str = str(API_DIR / "uploads")

    # Import TestFlight (optionnel, pour les testeurs externes) : clé API App Store Connect créée par l'équipe.
    ASC_ISSUER_ID: Optional[str] = None
    ASC_KEY_ID: Optional[str] = None
    ASC_PRIVATE_KEY_PATH: Optional[str] = None  # chemin du fichier .p8
    ASC_APP_ID: Optional[str] = None  # identifiant Apple de l'app (nombre)
    TESTFLIGHT_SYNC_MINUTES: int = 15

    @property
    def asc_private_key(self) -> Optional[str]:
        if not self.ASC_PRIVATE_KEY_PATH:
            return None
        path = Path(self.ASC_PRIVATE_KEY_PATH)
        return path.read_text(encoding="utf-8") if path.is_file() else None

    @model_validator(mode="after")
    def _check_production(self) -> "Settings":
        # Pas de valeur par défaut pour le secret : une session signée avec un secret connu serait falsifiable.
        if self.ENVIRONMENT == "production":
            if not self.HQ_SESSION_SECRET or len(self.HQ_SESSION_SECRET) < 32:
                raise ValueError("HQ_SESSION_SECRET (32 caractères au moins) est obligatoire en production.")
            if self.HQ_DEV_LOGIN:
                raise ValueError("HQ_DEV_LOGIN est interdit en production.")
            if self.SMTP_HOST and "localhost" in self.HQ_PUBLIC_URL:
                raise ValueError("HQ_PUBLIC_URL doit donner l'adresse publique de HQ : les liens envoyés par email y mènent.")
        return self

    @cached_property
    def session_secret(self) -> str:
        if self.HQ_SESSION_SECRET:
            return self.HQ_SESSION_SECRET
        if self.ENVIRONMENT == "development":
            # En local seulement : l'application crée elle-même un secret et le garde dans un fichier ignoré par git,
            # pour que les sessions survivent aux redémarrages du serveur.
            path = API_DIR / ".dev-session-secret"
            if not path.exists():
                path.write_text(secrets.token_urlsafe(32), encoding="utf-8")
            return path.read_text(encoding="utf-8").strip()
        return secrets.token_urlsafe(32)

    @property
    def dev_login_enabled(self) -> bool:
        return self.HQ_DEV_LOGIN and self.ENVIRONMENT != "production"

    @property
    def async_database_url(self) -> str:
        return to_async_url(self.DATABASE_URL)

    @property
    def heads_initiaux(self) -> List[str]:
        return [e.strip().lower() for e in self.HQ_HEADS_INITIAUX.split(",") if e.strip()]

    @property
    def origines(self) -> List[str]:
        return [o.strip().rstrip("/") for o in self.HQ_ORIGINES.split(",") if o.strip()]


settings = Settings()
