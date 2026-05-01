"""Integration tests for POST /auth/activate.

A pending user (created via OAuth) submits a user-generated invite code to
activate their account and receive a new JWT with status='active'.

Each test runs inside a rolled-back transaction for isolation.
Requires a running PostgreSQL on TEST_DATABASE_URL (port 5433).
"""

from __future__ import annotations

import os

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

JWT_SECRET = "test-secret"
ADMIN_SECRET = "test-admin-secret"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def activate_engine() -> Engine:
    engine = get_engine(TEST_DATABASE_URL)
    run_migrations(engine)
    yield engine
    engine.dispose()


@pytest.fixture()
def client(activate_engine: Engine):
    connection = activate_engine.connect()
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


def _register_active_user(
    client: TestClient,
    *,
    email: str = "active@example.com",
    password: str = "StrongPass123!",
    display_name: str = "Active User",
) -> str:
    """Register via email+invite (status=active) and return JWT."""
    resp = client.post(
        "/admin/invite-codes",
        json={"count": 1},
        headers={"X-Admin-Secret": ADMIN_SECRET},
    )
    assert resp.status_code == 201, resp.text
    invite_code = resp.json()["codes"][0]["code"]

    reg = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": password,
            "display_name": display_name,
            "invite_code": invite_code,
        },
    )
    assert reg.status_code == 201, reg.text

    token_resp = client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    assert token_resp.status_code == 200, token_resp.text
    return token_resp.json()["access_token"]


def _create_pending_user_token(
    client: TestClient,
    token_service: JwtTokenService,
    *,
    email: str = "pending@example.com",
    display_name: str = "Pending User",
) -> str:
    """
    Simulate what the OAuth callback does: insert a pending user directly via
    the register endpoint is not possible (register always creates active users),
    so we craft a pending JWT manually using the same token_service.

    We first register the user normally (active), then craft a *pending* token
    for that user_id to simulate an OAuth-created account awaiting activation.
    """
    # Register the user via normal flow to get a real user_id in the DB
    admin_resp = client.post(
        "/admin/invite-codes",
        json={"count": 1},
        headers={"X-Admin-Secret": ADMIN_SECRET},
    )
    assert admin_resp.status_code == 201
    invite_code = admin_resp.json()["codes"][0]["code"]

    reg = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "StrongPass123!",
            "display_name": display_name,
            "invite_code": invite_code,
        },
    )
    assert reg.status_code == 201, reg.text
    user_id = reg.json()["user_id"]

    # Craft a pending JWT for this user (simulating OAuth registration)
    return token_service.create_access_token(user_id, status="pending")


# ---------------------------------------------------------------------------
# Tests: POST /auth/activate
# ---------------------------------------------------------------------------


class TestActivateAccount:
    def test_activate_returns_200_with_new_token(self, client: TestClient) -> None:
        token_service = JwtTokenService(secret=JWT_SECRET, expire_minutes=60)
        active_token = _register_active_user(client, email="activator1@example.com")

        # Generate a user invite code
        code_resp = client.post(
            "/auth/invite-codes",
            headers={"Authorization": f"Bearer {active_token}"},
        )
        assert code_resp.status_code == 201, code_resp.text
        invite_code = code_resp.json()["code"]

        pending_token = _create_pending_user_token(
            client,
            token_service,
            email="pending1@example.com",
        )

        resp = client.post(
            "/auth/activate",
            json={"invite_code": invite_code},
            headers={"Authorization": f"Bearer {pending_token}"},
        )

        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_activated_token_has_active_status(self, client: TestClient) -> None:
        token_service = JwtTokenService(secret=JWT_SECRET, expire_minutes=60)
        active_token = _register_active_user(client, email="activator2@example.com")

        code_resp = client.post(
            "/auth/invite-codes",
            headers={"Authorization": f"Bearer {active_token}"},
        )
        invite_code = code_resp.json()["code"]

        pending_token = _create_pending_user_token(
            client,
            token_service,
            email="pending2@example.com",
        )

        resp = client.post(
            "/auth/activate",
            json={"invite_code": invite_code},
            headers={"Authorization": f"Bearer {pending_token}"},
        )
        assert resp.status_code == 200

        new_token = resp.json()["access_token"]
        payload = token_service.decode_token_full(new_token)
        assert payload["status"] == "active"

    def test_activate_rejects_unknown_invite_code(self, client: TestClient) -> None:
        token_service = JwtTokenService(secret=JWT_SECRET, expire_minutes=60)
        pending_token = _create_pending_user_token(
            client,
            token_service,
            email="pending3@example.com",
        )

        resp = client.post(
            "/auth/activate",
            json={"invite_code": "NONEXISTENT-CODE"},
            headers={"Authorization": f"Bearer {pending_token}"},
        )

        assert resp.status_code == 422, resp.text

    def test_activate_rejects_already_used_invite_code(self, client: TestClient) -> None:
        token_service = JwtTokenService(secret=JWT_SECRET, expire_minutes=60)
        active_token = _register_active_user(client, email="activator4@example.com")

        code_resp = client.post(
            "/auth/invite-codes",
            headers={"Authorization": f"Bearer {active_token}"},
        )
        invite_code = code_resp.json()["code"]

        # First pending user activates successfully
        pending_token_1 = _create_pending_user_token(
            client,
            token_service,
            email="pending4a@example.com",
        )
        r1 = client.post(
            "/auth/activate",
            json={"invite_code": invite_code},
            headers={"Authorization": f"Bearer {pending_token_1}"},
        )
        assert r1.status_code == 200

        # Second pending user tries the same (now exhausted) code
        pending_token_2 = _create_pending_user_token(
            client,
            token_service,
            email="pending4b@example.com",
        )
        r2 = client.post(
            "/auth/activate",
            json={"invite_code": invite_code},
            headers={"Authorization": f"Bearer {pending_token_2}"},
        )
        assert r2.status_code == 422

    def test_activate_requires_authentication(self, client: TestClient) -> None:
        resp = client.post(
            "/auth/activate",
            json={"invite_code": "SOME-CODE"},
        )
        assert resp.status_code == 401

    def test_activate_rejects_active_token(self, client: TestClient) -> None:
        """An already-active user cannot call /activate (endpoint requires pending token)."""
        active_token = _register_active_user(client, email="activator6@example.com")

        resp = client.post(
            "/auth/activate",
            json={"invite_code": "ANY-CODE"},
            headers={"Authorization": f"Bearer {active_token}"},
        )
        # active token is not accepted by get_pending_user_id dependency
        assert resp.status_code == 403
