"""Integration tests for POST /auth/oauth/google/link endpoint.

Tests the full HTTP → route → use case → repository flow with a real
PostgreSQL database and a FakeOAuthClient (no real Google API calls).
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, event
from sqlalchemy.orm import Session

from auth.api.app import create_auth_app
from auth.api.dependencies import (
    get_auth_uow,
    get_google_oauth_client,
    get_password_hasher,
    get_token_service,
)
from auth.domain.oauth import OAuthUserInfo
from auth.infrastructure.bcrypt_password_hasher import BcryptPasswordHasher
from auth.infrastructure.database import (
    TEST_DATABASE_URL,
    create_tables,
    drop_tables,
    get_engine,
)
from auth.infrastructure.jwt_token_service import JwtTokenService
from auth.infrastructure.sqlalchemy_unit_of_work import SqlAlchemyUnitOfWork
from tests.auth.fakes.fake_unit_of_work import FakeOAuthClient

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

JWT_SECRET = "test-link-api-secret-32chars!!"

GOOGLE_LINK_USER_INFO = OAuthUserInfo(
    provider="google",
    provider_user_id="google-sub-link-789",
    email="link-user@google.com",
    display_name="Link User Google",
)


@pytest.fixture(scope="module")
def link_api_engine() -> Engine:
    engine = get_engine(TEST_DATABASE_URL)
    drop_tables(engine)
    create_tables(engine)
    yield engine
    drop_tables(engine)
    engine.dispose()


@pytest.fixture()
def link_api_client(link_api_engine: Engine):
    """TestClient with FakeOAuthClient for Google link endpoint tests."""
    connection = link_api_engine.connect()
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

    def _test_uow():
        uow = SqlAlchemyUnitOfWork(factory)  # type: ignore[arg-type]
        yield uow

    password_hasher = BcryptPasswordHasher(rounds=4)
    token_service = JwtTokenService(secret=JWT_SECRET, expire_minutes=60)
    fake_oauth = FakeOAuthClient(user_info=GOOGLE_LINK_USER_INFO)

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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _register_and_get_token(
    client: TestClient,
    email: str = "link-user@example.com",
    password: str = "StrongPass123!",
    display_name: str = "LinkUser",
) -> tuple[dict, str]:
    """Register, login, return (user_data, access_token)."""
    resp = client.post(
        "/auth/register",
        json={"email": email, "password": password, "display_name": display_name},
    )
    assert resp.status_code == 201, resp.text
    user_data = resp.json()

    resp = client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]

    return user_data, token


# ---------------------------------------------------------------------------
# Tests: POST /auth/oauth/google/link
# ---------------------------------------------------------------------------


class TestGoogleOAuthLink:
    """POST /auth/oauth/google/link — links Google to authenticated user."""

    def test_links_google_account_successfully(
        self, link_api_client: TestClient
    ) -> None:
        _, token = _register_and_get_token(link_api_client)

        resp = link_api_client.post(
            "/auth/oauth/google/link",
            json={"code": "google-auth-code", "state": "some-state"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["message"] == "Google account linked successfully"

    def test_credentials_show_google_after_linking(
        self, link_api_client: TestClient
    ) -> None:
        _, token = _register_and_get_token(
            link_api_client, email="link-verify@example.com"
        )

        # Link Google
        resp = link_api_client.post(
            "/auth/oauth/google/link",
            json={"code": "google-auth-code", "state": "some-state"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200

        # Verify credentials now include Google
        resp = link_api_client.get(
            "/auth/credentials",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_count"] == 2
        providers = {c["provider"] for c in data["credentials"]}
        assert providers == {"local", "google"}

    def test_requires_authentication(self, link_api_client: TestClient) -> None:
        resp = link_api_client.post(
            "/auth/oauth/google/link",
            json={"code": "auth-code", "state": "some-state"},
        )
        assert resp.status_code == 401

    def test_returns_422_when_provider_already_linked(
        self, link_api_client: TestClient
    ) -> None:
        _, token = _register_and_get_token(
            link_api_client, email="double-link@example.com"
        )

        # First link succeeds
        resp = link_api_client.post(
            "/auth/oauth/google/link",
            json={"code": "google-auth-code", "state": "some-state"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200

        # Second link with same provider should fail
        resp = link_api_client.post(
            "/auth/oauth/google/link",
            json={"code": "google-auth-code-2", "state": "some-state"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422
        assert "already has a credential" in resp.json()["detail"]

    def test_returns_409_when_google_account_owned_by_another_user(
        self, link_api_client: TestClient
    ) -> None:
        # User A registers and links the Google account
        _, token_a = _register_and_get_token(
            link_api_client, email="owner-a@example.com", display_name="OwnerA"
        )
        resp = link_api_client.post(
            "/auth/oauth/google/link",
            json={"code": "google-auth-code", "state": "some-state"},
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert resp.status_code == 200

        # User B registers and tries to link the SAME Google account
        _, token_b = _register_and_get_token(
            link_api_client, email="claimant-b@example.com", display_name="ClaimantB"
        )
        resp = link_api_client.post(
            "/auth/oauth/google/link",
            json={"code": "google-auth-code", "state": "some-state"},
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert resp.status_code == 409
        assert "already connected to another user" in resp.json()["detail"]
