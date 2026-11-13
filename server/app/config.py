"""Réglages lus dans l'environnement (.env). Aucun secret n'est écrit ici."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="HQ_", extra="ignore")

    database_url: str = "postgresql+asyncpg://localhost/nyuman_hq"
    # Clé de signature des sessions. La valeur par défaut ne sert qu'en local.
    session_secret: str = "dev-local-seulement"
    # En local, on choisit son profil sans mot de passe. À couper en ligne.
    dev_login: bool = True
    cors_origins: str = "http://localhost:5180"
    # Dossier des fichiers envoyés (en ligne : stockage S3 plus tard).
    upload_dir: str = "uploads"
    max_upload_mb: int = 25
    # Visio
    jitsi_base: str = "https://meet.jit.si"
    google_client_id: str = ""
    google_client_secret: str = ""
    google_refresh_token: str = ""


settings = Settings()
