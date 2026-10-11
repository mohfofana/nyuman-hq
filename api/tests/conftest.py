import os

# Réglages de test, posés avant tout import de l'application.
os.environ.update(
    {
        "ENVIRONMENT": "test",
        "DATABASE_URL": "sqlite+aiosqlite://",
        "HQ_SESSION_SECRET": "secret-de-test-qui-fait-plus-de-32-caracteres",
        "HQ_DEV_LOGIN": "true",
        "HQ_HEADS_INITIAUX": "",
        "GOOGLE_CLIENT_ID": "client-test.apps.googleusercontent.com",
        "NYUMAN_DB_LECTURE_URL": "",
        "NYUMAN_API_URL": "",
        "NYUMAN_STATS_KEY": "",
        "HQ_WEB_DIR": "dossier-absent",
    }
)

from datetime import datetime, timezone  # noqa: E402

import httpx  # noqa: E402
import pytest  # noqa: E402
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine  # noqa: E402
from sqlalchemy.pool import NullPool, StaticPool  # noqa: E402

import adapters.entities  # noqa: E402,F401
from adapters.common.ports.out.local_capture_storage import LocalCaptureStorage  # noqa: E402
from adapters.common.providers import (  # noqa: E402
    get_capture_storage,
    get_google_verifier,
    get_mail_sender,
    get_stats_gateway,
    get_testflight_gateway,
)
from use_cases.common.ports.out.testflight_gateway import RetourSource, TestflightGateway  # noqa: E402
from core.config import to_async_url  # noqa: E402
from core.database import Base, get_async_session  # noqa: E402
from domain.value_objects.kpi import KpiSnapshot  # noqa: E402
from drivers.main import create_app  # noqa: E402
from drivers.seed import seed  # noqa: E402
from use_cases.common.ports.out.google_token_verifier import GoogleIdentity, GoogleTokenVerifier  # noqa: E402
from use_cases.common.ports.out.mail_sender import MailSender  # noqa: E402
from use_cases.common.ports.out.stats_gateway import StatsGateway  # noqa: E402
from use_cases.core.membre.exceptions.membre_exceptions import ConnexionGoogleInvalideException  # noqa: E402

HEAD_EMAIL = "head@example.com"
ORIGIN = "http://localhost:5173"


class FakeStatsGateway(StatsGateway):
    def __init__(self):
        self.next = KpiSnapshot.from_totals(
            {
                "utilisateurs_inscrits": 1240,
                "pros_actifs": 38,
                "reservations_7j": 212,
                "acomptes_7j_fcfa": 486000,
                "revenu_nyuman_7j_fcfa": 23900,
            },
            datetime.now(timezone.utc),
        )

    async def snapshot(self) -> KpiSnapshot:
        return self.next


class FakeGoogleVerifier(GoogleTokenVerifier):
    """Accepte les jetons « ok:<email>:<nom> », refuse le reste."""

    async def verify(self, credential: str) -> GoogleIdentity:
        parts = credential.split(":")
        if len(parts) != 3 or parts[0] != "ok":
            raise ConnexionGoogleInvalideException()
        return GoogleIdentity(email=parts[1], name=parts[2])


class FakeTestflight(TestflightGateway):
    """Pas de clé par défaut ; un test peut lui donner des retours à renvoyer."""

    def __init__(self):
        self.sources: list[RetourSource] = []
        self.is_configured = False

    @property
    def configured(self) -> bool:
        return self.is_configured

    async def fetch(self, limit: int = 50):
        return list(self.sources)

    async def download(self, url: str):
        return b"\x89PNG\r\n\x1a\n-capture-" + url.encode(), "image/png"


class FakeMailSender(MailSender):
    """Garde les emails au lieu de les envoyer."""

    def __init__(self):
        self.sent: list[dict] = []
        self.is_configured = True

    @property
    def configured(self) -> bool:
        return self.is_configured

    async def send(self, to: str, subject: str, text: str, html: str) -> None:
        self.sent.append({"to": to, "subject": subject, "text": text, "html": html})


@pytest.fixture
def mails() -> FakeMailSender:
    return FakeMailSender()


@pytest.fixture
def testflight() -> FakeTestflight:
    return FakeTestflight()


@pytest.fixture
def storage(tmp_path) -> LocalCaptureStorage:
    return LocalCaptureStorage(tmp_path)


# HQ_TEST_DATABASE_URL=postgresql://… : les mêmes tests sur un vrai Postgres, comme sur le serveur (sinon SQLite en mémoire).
TEST_DATABASE_URL = os.environ.get("HQ_TEST_DATABASE_URL")


@pytest.fixture
async def session_factory():
    if TEST_DATABASE_URL:
        engine = create_async_engine(to_async_url(TEST_DATABASE_URL), poolclass=NullPool)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    else:
        engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        await seed(session, [HEAD_EMAIL])
    yield factory
    await engine.dispose()


@pytest.fixture
def stats() -> FakeStatsGateway:
    return FakeStatsGateway()


@pytest.fixture
async def client(session_factory, stats, storage, testflight, mails):
    app = create_app(with_lifespan=False)

    async def _session():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_async_session] = _session
    app.dependency_overrides[get_stats_gateway] = lambda: stats
    app.dependency_overrides[get_google_verifier] = lambda: FakeGoogleVerifier()
    app.dependency_overrides[get_capture_storage] = lambda: storage
    app.dependency_overrides[get_testflight_gateway] = lambda: testflight
    app.dependency_overrides[get_mail_sender] = lambda: mails
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://hq.test", headers={"Origin": ORIGIN}) as c:
        yield c


async def login(client: httpx.AsyncClient, email: str = HEAD_EMAIL) -> dict:
    response = await client.post("/api/auth/dev", json={"email": email})
    assert response.status_code == 200, response.text
    return response.json()
