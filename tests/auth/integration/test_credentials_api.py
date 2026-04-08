"""Integration tests for GET /auth/credentials endpoint.

Uses the same test infrastructure as test_api.py: real PostgreSQL
with SAVEPOINT isolation.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, event
from sqlalchemy.orm import Session, sessionmaker

from auth.api.app import create_auth_app
from auth.api.dependencies import get_auth_uow, get_password_hasher, get_token_service
from auth.infrastructure.bcrypt_password_hasher import BcryptPasswordHasher
from auth.infrastructure.database import (
    TEST_DATABASE_URL,
    create_tables,
    drop_tables,
    get_engine,
)
from auth.infrastructure.jwt_token_service import JwtTokenService
from auth.infrastructure.sqlalchemy_unit_of_work import SqlAlchemyUnitOfWork

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

JWT_SECRET = "test-credentials-secret"


@pytest.fixture(scope="module")
def cred_api_engine() -> Engine:
    engine = get_engine(TEST_DATABASE_URL)
    drop_tables(engine)
    create_tables(engine)
    yield engine
    drop_tables(engine)
    engine.dispose()


@pytest.fixture()
def cred_api_client(cred_api_engine: Engine):
    """TestClient with SAVEPOINT isolation — same pattern as test_api.py."""
    connection = cred_api_engine.connect()
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
    email: str = "cred-user@example.com",
    password: str = "StrongPass123!",
    display_name: str = "CredUser",
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
# Tests
# ---------------------------------------------------------------------------


class TestGetCredentials:
    """GET /auth/credentials — returns sign-in methods for the current user."""

    def test_returns_credentials_for_local_user(
        self, cred_api_client: TestClient
    ) -> None:
        _, token = _register_and_get_token(cred_api_client)

        resp = cred_api_client.get(
            "/auth/credentials",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()

        assert data["user_email"] == "cred-user@example.com"
        assert data["user_display_name"] == "CredUser"
        assert data["total_count"] == 1
        assert data["has_local_credential"] is True

        creds = data["credentials"]
        assert len(creds) == 1
        assert creds[0]["provider"] == "local"
        assert creds[0]["provider_display_name"] == "Email & Password"
        assert creds[0]["provider_user_id"] == "cred-user@example.com"
        assert creds[0]["is_removable"] is False  # sole credential

    def test_requires_authentication(self, cred_api_client: TestClient) -> None:
        resp = cred_api_client.get("/auth/credentials")
        assert resp.status_code == 401

    def test_rejects_invalid_token(self, cred_api_client: TestClient) -> None:
        resp = cred_api_client.get(
            "/auth/credentials",
            headers={"Authorization": "Bearer invalid-garbage"},
        )
        assert resp.status_code == 401

    def test_response_has_expected_schema_fields(
        self, cred_api_client: TestClient
    ) -> None:
        _, token = _register_and_get_token(
            cred_api_client, email="schema-test@example.com"
        )
        resp = cred_api_client.get(
            "/auth/credentials",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = resp.json()

        # Top-level fields
        assert "user_email" in data
        assert "user_display_name" in data
        assert "credentials" in data
        assert "total_count" in data
        assert "has_local_credential" in data

        # Credential fields
        cred = data["credentials"][0]
        assert "credential_id" in cred
        assert "provider" in cred
        assert "provider_display_name" in cred
        assert "provider_user_id" in cred
        assert "is_removable" in cred
