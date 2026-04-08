"""Auth API integration tests: test FastAPI endpoints against real PostgreSQL.

Uses ``httpx`` sync TestClient + the test database (port 5433).
Each test runs inside a rolled-back transaction for isolation.

Follows the same SAVEPOINT isolation pattern as project_collaboration API tests.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Connection, Engine, event
from sqlalchemy.orm import Session, sessionmaker

from auth.api.app import create_auth_app
from auth.api.dependencies import get_auth_uow, get_password_hasher, get_token_service
from auth.infrastructure.bcrypt_password_hasher import BcryptPasswordHasher
from auth.infrastructure.database import (
    TEST_DATABASE_URL,
    get_engine,
)
from auth.infrastructure.jwt_token_service import JwtTokenService
from auth.infrastructure.sqlalchemy_unit_of_work import SqlAlchemyUnitOfWork
from shared_kernel.migration import run_migrations


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

JWT_SECRET = "test-secret"


@pytest.fixture(scope="module")
def auth_api_engine() -> Engine:
    engine = get_engine(TEST_DATABASE_URL)
    run_migrations(engine)
    yield engine
    engine.dispose()


@pytest.fixture()
def auth_api_client(auth_api_engine: Engine):
    """Create a TestClient whose UoW is bound to a rolled-back transaction.

    A single session is shared across all requests within one test.
    Same pattern as project_collaboration API tests: override rollback/close
    to no-ops so UoW.__exit__ doesn't destroy the shared session.
    """
    connection = auth_api_engine.connect()
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
        """Always returns the same shared session."""

        def __call__(self) -> Session:
            return session

    factory = _TestSessionFactory()

    app = create_auth_app()

    # Override dependencies
    def _test_uow():
        uow = SqlAlchemyUnitOfWork(factory)  # type: ignore[arg-type]
        yield uow

    password_hasher = BcryptPasswordHasher(rounds=4)  # fast rounds for tests
    token_service = JwtTokenService(secret=JWT_SECRET, expire_minutes=60)

    app.dependency_overrides[get_auth_uow] = _test_uow
    app.dependency_overrides[get_password_hasher] = lambda: password_hasher
    app.dependency_overrides[get_token_service] = lambda: token_service

    client = TestClient(app)
    yield client

    _real_close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _register_user(
    client: TestClient,
    email: str = "alice@example.com",
    password: str = "StrongPass123!",
    display_name: str = "Alice",
) -> dict:
    """Register a user and return the response JSON."""
    resp = client.post(
        "/auth/register",
        json={"email": email, "password": password, "display_name": display_name},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _login(
    client: TestClient,
    email: str = "alice@example.com",
    password: str = "StrongPass123!",
) -> dict:
    """Login and return the response JSON."""
    resp = client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    return resp.json()


def _register_and_get_token(
    client: TestClient,
    email: str = "alice@example.com",
    password: str = "StrongPass123!",
    display_name: str = "Alice",
) -> tuple[dict, str]:
    """Register a user, login, and return (user_data, access_token)."""
    user_data = _register_user(
        client, email=email, password=password, display_name=display_name
    )
    login_data = _login(client, email=email, password=password)
    return user_data, login_data["access_token"]


# ---------------------------------------------------------------------------
# Tests: Register
# ---------------------------------------------------------------------------


class TestRegister:
    def test_register_returns_201_with_user_info(
        self, auth_api_client: TestClient
    ) -> None:
        data = _register_user(auth_api_client)
        assert "user_id" in data
        assert data["email"] == "alice@example.com"
        assert data["display_name"] == "Alice"

    def test_register_normalizes_email(self, auth_api_client: TestClient) -> None:
        data = _register_user(
            auth_api_client, email="  BOB@Example.COM  ", display_name="Bob"
        )
        assert data["email"] == "bob@example.com"

    def test_register_duplicate_email_returns_422(
        self, auth_api_client: TestClient
    ) -> None:
        _register_user(auth_api_client, email="dup@example.com", display_name="First")
        resp = auth_api_client.post(
            "/auth/register",
            json={
                "email": "dup@example.com",
                "password": "StrongPass123!",
                "display_name": "Second",
            },
        )
        assert resp.status_code == 422
        assert "already registered" in resp.json()["detail"].lower()

    def test_register_missing_fields_returns_422(
        self, auth_api_client: TestClient
    ) -> None:
        # Missing password
        resp = auth_api_client.post(
            "/auth/register",
            json={"email": "test@example.com", "display_name": "Test"},
        )
        assert resp.status_code == 422

    def test_register_empty_email_returns_422(
        self, auth_api_client: TestClient
    ) -> None:
        resp = auth_api_client.post(
            "/auth/register",
            json={"email": "", "password": "pass", "display_name": "Test"},
        )
        assert resp.status_code == 422

    def test_register_empty_display_name_returns_422(
        self, auth_api_client: TestClient
    ) -> None:
        resp = auth_api_client.post(
            "/auth/register",
            json={"email": "x@y.com", "password": "pass", "display_name": ""},
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Tests: Login
# ---------------------------------------------------------------------------


class TestLogin:
    def test_login_returns_access_token(self, auth_api_client: TestClient) -> None:
        _register_user(auth_api_client, email="login@example.com")
        resp = auth_api_client.post(
            "/auth/login",
            json={"email": "login@example.com", "password": "StrongPass123!"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0

    def test_login_wrong_password_returns_422(
        self, auth_api_client: TestClient
    ) -> None:
        _register_user(auth_api_client, email="wrongpw@example.com")
        resp = auth_api_client.post(
            "/auth/login",
            json={"email": "wrongpw@example.com", "password": "WrongPassword!"},
        )
        assert resp.status_code == 422
        assert "invalid" in resp.json()["detail"].lower()

    def test_login_nonexistent_email_returns_422(
        self, auth_api_client: TestClient
    ) -> None:
        resp = auth_api_client.post(
            "/auth/login",
            json={"email": "nobody@example.com", "password": "pass"},
        )
        assert resp.status_code == 422
        assert "invalid" in resp.json()["detail"].lower()

    def test_login_missing_fields_returns_422(
        self, auth_api_client: TestClient
    ) -> None:
        resp = auth_api_client.post(
            "/auth/login",
            json={"email": "test@example.com"},
        )
        assert resp.status_code == 422

    def test_login_token_is_valid_jwt(self, auth_api_client: TestClient) -> None:
        """Verify the returned token can be decoded back to the user_id."""
        user_data = _register_user(auth_api_client, email="jwt@example.com")
        resp = auth_api_client.post(
            "/auth/login",
            json={"email": "jwt@example.com", "password": "StrongPass123!"},
        )
        assert resp.status_code == 200
        token = resp.json()["access_token"]

        # Decode the token to verify it contains the correct user_id
        service = JwtTokenService(secret=JWT_SECRET)
        decoded_user_id = service.decode_token(token)
        assert decoded_user_id == user_data["user_id"]

    def test_login_email_is_case_insensitive(self, auth_api_client: TestClient) -> None:
        _register_user(auth_api_client, email="CaseTest@Example.com")
        resp = auth_api_client.post(
            "/auth/login",
            json={"email": "casetest@example.com", "password": "StrongPass123!"},
        )
        assert resp.status_code == 200
        assert "access_token" in resp.json()


# ---------------------------------------------------------------------------
# Tests: GET /auth/me
# ---------------------------------------------------------------------------


class TestGetMe:
    def test_me_returns_current_user_info(self, auth_api_client: TestClient) -> None:
        user_data, token = _register_and_get_token(
            auth_api_client, email="me@example.com", display_name="MeUser"
        )
        resp = auth_api_client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["user_id"] == user_data["user_id"]
        assert data["email"] == "me@example.com"
        assert data["display_name"] == "MeUser"

    def test_me_without_token_returns_401(self, auth_api_client: TestClient) -> None:
        resp = auth_api_client.get("/auth/me")
        assert resp.status_code == 401

    def test_me_with_invalid_token_returns_401(
        self, auth_api_client: TestClient
    ) -> None:
        resp = auth_api_client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid-garbage-token"},
        )
        assert resp.status_code == 401

    def test_me_with_malformed_header_returns_401(
        self, auth_api_client: TestClient
    ) -> None:
        resp = auth_api_client.get(
            "/auth/me",
            headers={"Authorization": "Token abc123"},
        )
        assert resp.status_code == 401
