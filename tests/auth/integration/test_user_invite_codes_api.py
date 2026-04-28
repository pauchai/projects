"""Integration tests for POST /auth/invite-codes (user-generated invite codes).

Each test runs inside a rolled-back transaction for isolation.
Requires a running PostgreSQL on TEST_DATABASE_URL (port 5433).
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, event
from sqlalchemy.orm import Session

from auth.api.app import create_auth_app
from auth.api.dependencies import get_auth_uow, get_password_hasher, get_token_service
from auth.infrastructure.bcrypt_password_hasher import BcryptPasswordHasher
from auth.infrastructure.database import TEST_DATABASE_URL, get_engine
from auth.infrastructure.jwt_token_service import JwtTokenService
from auth.infrastructure.sqlalchemy_unit_of_work import SqlAlchemyUnitOfWork
from shared_kernel.migration import run_migrations

import os

JWT_SECRET = "test-secret"
ADMIN_SECRET = "test-admin-secret"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def user_invite_engine() -> Engine:
    engine = get_engine(TEST_DATABASE_URL)
    run_migrations(engine)
    yield engine
    engine.dispose()


@pytest.fixture()
def client(user_invite_engine: Engine):
    connection = user_invite_engine.connect()
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

    os.environ["ADMIN_SECRET"] = ADMIN_SECRET

    yield TestClient(app)

    _real_close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _register_and_login(
    client: TestClient,
    *,
    email: str = "inviter@example.com",
    password: str = "StrongPass123!",
    display_name: str = "Inviter User",
) -> str:
    """Register a user (using an admin invite) and return a JWT token."""
    # Create an admin invite code first
    resp = client.post(
        "/admin/invite-codes",
        json={"count": 1},
        headers={"X-Admin-Secret": ADMIN_SECRET},
    )
    assert resp.status_code == 201, resp.text
    invite_code = resp.json()["codes"][0]["code"]

    client.post(
        "/auth/register",
        json={
            "email": email,
            "password": password,
            "display_name": display_name,
            "invite_code": invite_code,
        },
    )

    token_resp = client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    assert token_resp.status_code == 200, token_resp.text
    return token_resp.json()["access_token"]


# ---------------------------------------------------------------------------
# Tests: POST /auth/invite-codes
# ---------------------------------------------------------------------------


class TestUserCreateInviteCode:
    def test_returns_201_with_code_fields(self, client: TestClient) -> None:
        token = _register_and_login(client)

        resp = client.post(
            "/auth/invite-codes",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert "code" in data
        assert "expires_at" in data
        assert "max_uses" in data

    def test_code_is_single_use(self, client: TestClient) -> None:
        token = _register_and_login(client, email="inviter2@example.com")

        resp = client.post(
            "/auth/invite-codes",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        assert resp.json()["max_uses"] == 1

    def test_generated_code_can_be_used_to_register(self, client: TestClient) -> None:
        token = _register_and_login(client, email="inviter3@example.com")

        code_resp = client.post(
            "/auth/invite-codes",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert code_resp.status_code == 201
        code = code_resp.json()["code"]

        reg_resp = client.post(
            "/auth/register",
            json={
                "email": "invitee@example.com",
                "password": "StrongPass123!",
                "display_name": "Invitee",
                "invite_code": code,
            },
        )
        assert reg_resp.status_code == 201, reg_resp.text

    def test_generated_code_is_single_use_on_registration(
        self, client: TestClient
    ) -> None:
        token = _register_and_login(client, email="inviter4@example.com")

        code_resp = client.post(
            "/auth/invite-codes",
            headers={"Authorization": f"Bearer {token}"},
        )
        code = code_resp.json()["code"]

        # First use succeeds
        r1 = client.post(
            "/auth/register",
            json={
                "email": "first_invitee@example.com",
                "password": "StrongPass123!",
                "display_name": "First",
                "invite_code": code,
            },
        )
        assert r1.status_code == 201

        # Second use fails
        r2 = client.post(
            "/auth/register",
            json={
                "email": "second_invitee@example.com",
                "password": "StrongPass123!",
                "display_name": "Second",
                "invite_code": code,
            },
        )
        assert r2.status_code == 422

    def test_requires_authentication(self, client: TestClient) -> None:
        resp = client.post("/auth/invite-codes")
        assert resp.status_code == 401

    def test_rejects_invalid_token(self, client: TestClient) -> None:
        resp = client.post(
            "/auth/invite-codes",
            headers={"Authorization": "Bearer not-a-valid-token"},
        )
        assert resp.status_code == 401
