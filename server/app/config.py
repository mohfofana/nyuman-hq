"""Réglages lus dans l'environnement (.env). Aucun secret n'est écrit ici."""
import os

from pydantic_settings import BaseSettings, SettingsConfigDict


def _normalize_db(url: str) -> str:
    """Accepte l'adresse telle que l'hébergeur la donne (postgres://…) et la rend utilisable ici."""
    for prefix in ("postgresql+asyncpg://", ):
        if url.startswith(prefix):
            return url
    for prefix in ("postgresql://", "postgres://"):
        if url.startswith(prefix):
            return "postgresql+asyncpg://" + url[len(prefix):]
    return url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="HQ_", extra="ignore")

    database_url: str = "postgresql+asyncpg://localhost/nyuman_hq"
    # Clé de signature des sessions. La valeur par défaut ne sert qu'en local.
    session_secret: str = "dev-local-seulement"
    # En local, on choisit son profil sans mot de passe. À couper en ligne.
    dev_login: bool = True
    cors_origins: str = "http://localhost:5180"
    # Dossier du site compilé (web/dist) servi par le serveur en ligne. Vide = site servi à part (local).
    web_dir: str = ""
    # Dossier des fichiers envoyés (en ligne : stockage S3 plus tard).
    upload_dir: str = "uploads"
    max_upload_mb: int = 25
    # Visio
    jitsi_base: str = "https://meet.jit.si"
    # Adresse publique de HQ (sert à construire l'adresse de retour de Google). Vide = local.
    public_url: str = ""
    # Cookie de session : à mettre à true en ligne (HTTPS).
    cookie_secure: bool = False
    # Secours pour la toute première connexion en ligne : "adresse=identifiant,autre=identifiant".
    # À poser par Kevin, puis à retirer une fois les adresses remplies dans HQ.
    bootstrap_emails: str = ""
    # Envoi des liens de connexion par e-mail (compte @nyuman.app chez Netim).
    # Kevin pose l'identifiant et le mot de passe ; Kwame ne les lit jamais.
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    mail_from: str = ""  # ex. "Nyuman HQ <hq@nyuman.app>" ; vide = on prend smtp_user
    google_client_id: str = ""
    google_client_secret: str = ""
    google_refresh_token: str = ""
    # Réveil des agents (Claude lancé en arrière-plan quand on écrit à un agent)
    agent_wake: bool = False
    claude_bin: str = "claude"
    agent_daily_cap: int = 30
    agent_run_timeout_s: int = 240
    agent_max_budget_usd: float = 0.25
    # Agents dont la discussion Claude est déjà ouverte : HQ ne lance pas de copie, c'est elle qui répond.
    agent_wake_skip: str = ""
    # Délai laissé à une discussion ouverte pour répondre avant que la copie prenne le relais.
    agent_wake_grace_s: int = 180
    agent_workdir: str = ""  # dossier où tourne l'agent (sa mémoire d'équipe est liée à ce dossier)
    # Chiffres de l'app (totaux seulement, route /admin/hq-stats de nyuman-api). Clé posée par Kevin, jamais lue par Kwame.
    stats_url: str = ""  # ex. https://<api staging>/admin/hq-stats
    stats_key: str = ""


settings = Settings()

# Railway (et la plupart des hébergeurs) fournissent DATABASE_URL et PORT sans notre préfixe HQ_.
if not os.getenv("HQ_DATABASE_URL") and os.getenv("DATABASE_URL"):
    settings.database_url = os.environ["DATABASE_URL"]
settings.database_url = _normalize_db(settings.database_url)
