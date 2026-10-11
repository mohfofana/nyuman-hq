from pathlib import Path
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from adapters.common.ports.out.app_store_connect_gateway import AppStoreConnectGateway
from adapters.common.ports.out.google_id_token_verifier import GoogleIdTokenVerifier
from adapters.common.ports.out.local_capture_storage import LocalCaptureStorage
from adapters.common.ports.out.nyuman_db_stats_gateway import NyumanDbStatsGateway
from adapters.common.ports.out.nyuman_stats_gateway import NyumanStatsGateway
from adapters.common.ports.out.smtp_mail_sender import ConsoleMailSender, SmtpMailSender
from adapters.common.ports.out.xlsx_reader import XlsxReader
from core.config import settings, to_async_url
from use_cases.common.ports.out.google_token_verifier import GoogleTokenVerifier
from use_cases.common.ports.out.mail_sender import MailSender
from use_cases.common.ports.out.tableur_reader import TableurReader
from use_cases.common.ports.out.stats_gateway import StatsGateway
from use_cases.common.ports.out.testflight_gateway import CaptureStorage, TestflightGateway

# Dépendances FastAPI : les tests les remplacent par des doublures (aucun appel réseau pendant les tests).

_lecture_engine: Optional[AsyncEngine] = None


def _engine_lecture(url: str) -> AsyncEngine:
    # Compte de lecture seule créé par l'équipe (staging d'abord). Une ou deux connexions au plus.
    global _lecture_engine
    if _lecture_engine is None:
        async_url = to_async_url(url)
        connect_args = {"timeout": 5, "command_timeout": 5} if async_url.startswith("postgresql+asyncpg") else {}
        _lecture_engine = create_async_engine(
            async_url, pool_size=1, max_overflow=1, pool_pre_ping=True, connect_args=connect_args
        )
    return _lecture_engine


def get_stats_gateway() -> StatsGateway:
    if settings.NYUMAN_DB_LECTURE_URL:
        return NyumanDbStatsGateway(_engine_lecture(settings.NYUMAN_DB_LECTURE_URL), settings.KPI_CACHE_SECONDES)
    return NyumanStatsGateway(settings.NYUMAN_API_URL, settings.NYUMAN_STATS_KEY, settings.KPI_CACHE_SECONDES)


def get_google_verifier() -> GoogleTokenVerifier:
    return GoogleIdTokenVerifier(settings.GOOGLE_CLIENT_ID)


def get_mail_sender() -> MailSender:
    smtp = SmtpMailSender(
        settings.SMTP_HOST, settings.SMTP_PORT, settings.SMTP_USER, settings.SMTP_PASSWORD, settings.SMTP_FROM
    )
    # Sur un PC, sans boîte mail réglée : le lien s'affiche dans le journal du serveur.
    if not smtp.configured and settings.ENVIRONMENT == "development":
        return ConsoleMailSender()
    return smtp


def get_tableur_reader() -> TableurReader:
    return XlsxReader()


def get_capture_storage() -> CaptureStorage:
    return LocalCaptureStorage(Path(settings.HQ_UPLOADS_DIR))


def get_testflight_gateway() -> TestflightGateway:
    return AppStoreConnectGateway(
        settings.ASC_ISSUER_ID, settings.ASC_KEY_ID, settings.asc_private_key, settings.ASC_APP_ID
    )
