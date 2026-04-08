"""OAuth API integration tests: test OAuth endpoints against real PostgreSQL.

Uses ``httpx`` sync TestClient + test database (port 5433).
Google OAuth is simulated via ``FakeOAuthClient`` injected as a dependency
override — this tests the full HTTP → route → use case → repository flow
without hitting real Google APIs.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, event
from sqlalchemy.orm import Session, sessionmaker

from auth.api.app import create_auth_app
from auth.api.dependencies import (
    get_auth_uow,
    get_google_oauth_client,
    get_password_hasher,
    get_token_service,
)
from auth.domain.oauth import OAuthError, OAuthUserInfo
from auth.infrastructure.bcrypt_password_hasher import BcryptPasswordHasher
from auth.infrastructure.database import (
    TEST_DATABASE_URL,
    get_engine,
)
from auth.infrastructure.jwt_token_service import JwtTokenService
from auth.infrastructure.sqlalchemy_unit_of_work import SqlAlchemyUnitOfWork
from tests.auth.fakes.fake_unit_of_work import FakeOAuthClient
from shared_kernel.migration import run_migrations


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

JWT_SECRET = "test-secret-oauth"

GOOGLE_USER_INFO = OAuthUserInfo(
    provider="google",
    provider_user_id="google-sub-456",
    email="oauth-user@example.com",
    display_name="OAuth User",
)


@pytest.fixture(scope="module")
def oauth_api_engine() -> Engine:
    engine = get_engine(TEST_DATABASE_URL)
    run_migrations(engine)
    yield engine
    engine.dispose()


@pytest.fixture()
def oauth_api_client(oauth_api_engine: Engine):
    """TestClient with FakeOAuthClient injected for Google OAuth endpoints."""
    connection = oauth_api_engine.connect()
    transaction = connection.begin()

    session = Session(bind=connection)
    session.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(sess: Session, txn: object) -> None:
        if not sess.in_nested_transaction():
            sess.begin_nested()

    _real_close = session.close
    session.close = lambda: None  # type: ignore[assignment]
    session.rollback = lambda: None  # type: ignore[assignment]

    class _TestSessionFactory:
        def __call__(self) -> Session:
            return session

    factory = _TestSessionFactory()

    app = create_auth_app()

    # Override dependencies
    def _test_uow():
        uow = SqlAlchemyUnitOfWork(factory)  # type: ignore[arg-type]
        yield uow

    password_hasher = BcryptPasswordHasher(rounds=4)
    token_service = JwtTokenService(secret=JWT_SECRET, expire_minutes=60)
    fake_oauth = FakeOAuthClient(user_info=GOOGLE_USER_INFO)

    app.dependency_overrides[get_auth_uow] = _test_uow
    app.dependency_overrides[get_password_hasher] = lambda: password_hasher
    app.dependency_overrides[get_token_service] = lambda: token_service
    app.dependency_overrides[get_google_oauth_client] = lambda: fake_oauth

    client = TestClient(app)
    yield client

    _real_close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()


@pytest.fixture()
def oauth_unavailable_client(oauth_api_engine: Engine):
    """TestClient where Google OAuth is NOT configured (returns None)."""
    app = create_auth_app()
    app.dependency_overrides[get_google_oauth_client] = lambda: None

    client = TestClient(app)
    yield client


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _register_user(
    client: TestClient,
    email: str = "oauth-user@example.com",
    password: str = "StrongPass123!",
    display_name: str = "OAuth User",
) -> dict:
    resp = client.post(
        "/auth/register",
        json={"email": email, "password": password, "display_name": display_name},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


# ---------------------------------------------------------------------------
# Tests: GET /auth/oauth/google/available
# ---------------------------------------------------------------------------


class TestGoogleOAuthAvailable:
    def test_returns_available_true_when_configured(
        self, oauth_api_client: TestClient
    ) -> None:
        resp = oauth_api_client.get("/auth/oauth/google/available")
        assert resp.status_code == 200
        assert resp.json()["available"] is True

    def test_returns_available_false_when_not_configured(
        self, oauth_unavailable_client: TestClient
    ) -> None:
        resp = oauth_unavailable_client.get("/auth/oauth/google/available")
        assert resp.status_code == 200
        assert resp.json()["available"] is False


# ---------------------------------------------------------------------------
# Tests: GET /auth/oauth/google/authorize
# ---------------------------------------------------------------------------


class TestGoogleOAuthAuthorize:
    def test_returns_authorization_url_and_state(
        self, oauth_api_client: TestClient
    ) -> None:
        resp = oauth_api_client.get("/auth/oauth/google/authorize")
        assert resp.status_code == 200
        data = resp.json()
        assert "authorization_url" in data
        assert "state" in data
        assert len(data["state"]) > 0

    def test_returns_501_when_not_configured(
        self, oauth_unavailable_client: TestClient
    ) -> None:
        resp = oauth_unavailable_client.get("/auth/oauth/google/authorize")
        assert resp.status_code == 501
        assert "not configured" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Tests: POST /auth/oauth/google/callback
# ---------------------------------------------------------------------------


class TestGoogleOAuthCallback:
    def test_callback_creates_new_user_and_returns_token(
        self, oauth_api_client: TestClient
    ) -> None:
        resp = oauth_api_client.post(
            "/auth/oauth/google/callback",
            json={"code": "auth-code-new", "state": "random-state"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0

    def test_callback_returns_valid_jwt(self, oauth_api_client: TestClient) -> None:
        resp = oauth_api_client.post(
            "/auth/oauth/google/callback",
            json={"code": "auth-code-jwt", "state": "random-state"},
        )
        assert resp.status_code == 200
        token = resp.json()["access_token"]

        # Verify the token is a valid JWT
        service = JwtTokenService(secret=JWT_SECRET)
        user_id = service.decode_token(token)
        assert len(user_id) > 0

    def test_callback_links_credential_to_existing_user(
        self, oauth_api_client: TestClient
    ) -> None:
        # First register a user with the same email via email/password
        _register_user(oauth_api_client)

        # Now do OAuth callback — should link, not create duplicate
        resp = oauth_api_client.post(
            "/auth/oauth/google/callback",
            json={"code": "auth-code-link", "state": "random-state"},
        )
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_callback_returns_501_when_not_configured(
        self, oauth_unavailable_client: TestClient
    ) -> None:
        resp = oauth_unavailable_client.post(
            "/auth/oauth/google/callback",
            json={"code": "auth-code", "state": "random-state"},
        )
        assert resp.status_code == 501
        assert "not configured" in resp.json()["detail"].lower()

    def test_callback_missing_code_returns_422(
        self, oauth_api_client: TestClient
    ) -> None:
        resp = oauth_api_client.post(
            "/auth/oauth/google/callback",
            json={"state": "random-state"},
        )
        assert resp.status_code == 422

    def test_callback_empty_code_returns_422(
        self, oauth_api_client: TestClient
    ) -> None:
        resp = oauth_api_client.post(
            "/auth/oauth/google/callback",
            json={"code": "", "state": "random-state"},
        )
        assert resp.status_code == 422
