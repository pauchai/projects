"""Integration tests for POST /auth/local/set-password endpoint.

Tests the full HTTP → route → use case → repository flow with a real
PostgreSQL database.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, event
from sqlalchemy.orm import Session

from auth.api.app import create_auth_app
from auth.api.dependencies import get_auth_uow, get_password_hasher, get_token_service
from auth.domain.user import Credential, User
from auth.infrastructure.bcrypt_password_hasher import BcryptPasswordHasher
from auth.infrastructure.database import TEST_DATABASE_URL, get_engine
from auth.infrastructure.jwt_token_service import JwtTokenService
from auth.infrastructure.sqlalchemy_unit_of_work import SqlAlchemyUnitOfWork
from shared_kernel.migration import run_migrations

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

JWT_SECRET = "test-set-password-secret-32c!!"


@pytest.fixture(scope="module")
def set_password_engine() -> Engine:
    engine = get_engine(TEST_DATABASE_URL)
    run_migrations(engine)
    yield engine
    engine.dispose()


@pytest.fixture()
def set_password_client(set_password_engine: Engine):
    """TestClient with SAVEPOINT isolation."""
    connection = set_password_engine.connect()
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

    app.dependency_overrides[get_auth_uow] = _test_uow
    app.dependency_overrides[get_password_hasher] = lambda: password_hasher
    app.dependency_overrides[get_token_service] = lambda: token_service

    client = TestClient(app)
    yield client, session, factory

    _real_close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _register_and_get_token(
    client: TestClient,
    email: str,
    password: str = "StrongPass123!",
    display_name: str = "TestUser",
) -> tuple[dict, str]:
    """Register a local user, login, return (user_data, access_token)."""
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


def _create_oauth_only_user_and_get_token(
    session: Session,
    factory,
    token_service: JwtTokenService,
    user_id: str = "oauth-only-u1",
    email: str = "oauth-only@example.com",
) -> str:
    """Insert an OAuth-only user directly via UoW and return a JWT for them."""
    uow = SqlAlchemyUnitOfWork(factory)  # type: ignore[arg-type]
    with uow:
        user = User(user_id=user_id, email=email, display_name="OAuthUser")
        google_cred = Credential(
            credential_id=f"cred-google-{user_id}",
            user_id=user_id,
            provider="google",
            provider_user_id="google-sub-oauth-only",
            hashed_secret=None,
        )
        user.add_credential(google_cred)
        uow.users.save(user)
        uow.commit()
    return token_service.create_access_token(user_id)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestSetPassword:
    """POST /auth/local/set-password"""

    def test_sets_password_for_oauth_only_user(self, set_password_client) -> None:
        client, session, factory = set_password_client
        token_service = JwtTokenService(secret=JWT_SECRET, expire_minutes=60)
        token = _create_oauth_only_user_and_get_token(
            session,
            factory,
            token_service,
            user_id="sp-oauth-1",
            email="sp-oauth-1@example.com",
        )

        resp = client.post(
            "/auth/local/set-password",
            json={"password": "NewSecurePass1!"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["message"] == "Password set successfully"

    def test_can_login_with_password_after_setting(self, set_password_client) -> None:
        client, session, factory = set_password_client
        token_service = JwtTokenService(secret=JWT_SECRET, expire_minutes=60)
        token = _create_oauth_only_user_and_get_token(
            session,
            factory,
            token_service,
            user_id="sp-oauth-2",
            email="sp-login-2@example.com",
        )

        # Set password
        resp = client.post(
            "/auth/local/set-password",
            json={"password": "MyPassword123!"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200

        # Now login with email + password
        resp = client.post(
            "/auth/login",
            json={"email": "sp-login-2@example.com", "password": "MyPassword123!"},
        )
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_credentials_show_local_after_setting(self, set_password_client) -> None:
        client, session, factory = set_password_client
        token_service = JwtTokenService(secret=JWT_SECRET, expire_minutes=60)
        token = _create_oauth_only_user_and_get_token(
            session,
            factory,
            token_service,
            user_id="sp-oauth-3",
            email="sp-creds-3@example.com",
        )

        client.post(
            "/auth/local/set-password",
            json={"password": "Pass123!"},
            headers={"Authorization": f"Bearer {token}"},
        )

        resp = client.get(
            "/auth/credentials",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        providers = {c["provider"] for c in data["credentials"]}
        assert "local" in providers
        assert data["has_local_credential"] is True

    def test_local_credential_shows_email_in_provider_user_id(
        self, set_password_client
    ) -> None:
        """After set-password, credentials endpoint returns email (not UUID) for local."""
        client, session, factory = set_password_client
        token_service = JwtTokenService(secret=JWT_SECRET, expire_minutes=60)
        email = "sp-display-4@example.com"
        token = _create_oauth_only_user_and_get_token(
            session,
            factory,
            token_service,
            user_id="sp-oauth-4",
            email=email,
        )

        client.post(
            "/auth/local/set-password",
            json={"password": "Pass123!"},
            headers={"Authorization": f"Bearer {token}"},
        )

        resp = client.get(
            "/auth/credentials",
            headers={"Authorization": f"Bearer {token}"},
        )
        creds = resp.json()["credentials"]
        local_cred = next(c for c in creds if c["provider"] == "local")
        assert local_cred["provider_user_id"] == email  # email displayed, not UUID

    def test_requires_authentication(self, set_password_client) -> None:
        client, _, __ = set_password_client
        resp = client.post(
            "/auth/local/set-password",
            json={"password": "Pass123!"},
        )
        assert resp.status_code == 401

    def test_returns_422_when_user_already_has_local(self, set_password_client) -> None:
        client, _, __ = set_password_client
        _, token = _register_and_get_token(client, email="sp-already-local@example.com")

        resp = client.post(
            "/auth/local/set-password",
            json={"password": "AnotherPass123!"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422
        assert "already has local credentials" in resp.json()["detail"]
