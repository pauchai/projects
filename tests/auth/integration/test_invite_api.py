"""Integration tests for invite code API endpoints.

Covers:
  POST /admin/invite-codes  — admin generates codes (protected by ADMIN_SECRET header)
  POST /auth/register       — registration now requires invite_code

Uses the same SAVEPOINT isolation pattern as test_api.py.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Connection, Engine, event
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
def invite_api_engine() -> Engine:
    engine = get_engine(TEST_DATABASE_URL)
    run_migrations(engine)
    yield engine
    engine.dispose()


@pytest.fixture()
def invite_api_client(invite_api_engine: Engine):
    connection = invite_api_engine.connect()
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

    import os

    os.environ["ADMIN_SECRET"] = ADMIN_SECRET

    client = TestClient(app)
    yield client

    _real_close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _create_invite_codes(
    client: TestClient,
    count: int = 1,
    *,
    secret: str = ADMIN_SECRET,
) -> dict:
    resp = client.post(
        "/admin/invite-codes",
        json={"count": count},
        headers={"X-Admin-Secret": secret},
    )
    return resp


def _register_with_invite(
    client: TestClient,
    invite_code: str,
    *,
    email: str = "newuser@example.com",
    password: str = "StrongPass123!",
    display_name: str = "New User",
) -> dict:
    return client.post(
        "/auth/register",
        json={
            "email": email,
            "password": password,
            "display_name": display_name,
            "invite_code": invite_code,
        },
    )


# ---------------------------------------------------------------------------
# Tests: POST /admin/invite-codes
# ---------------------------------------------------------------------------


class TestAdminCreateInviteCodes:
    def test_returns_201_with_codes(self, invite_api_client: TestClient) -> None:
        resp = _create_invite_codes(invite_api_client, count=3)
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert len(data["codes"]) == 3

    def test_each_code_has_expected_fields(self, invite_api_client: TestClient) -> None:
        resp = _create_invite_codes(invite_api_client, count=1)
        assert resp.status_code == 201
        code = resp.json()["codes"][0]
        assert "code_id" in code
        assert "code" in code
        assert code["uses_left"] == 1
        assert code["max_uses"] == 1
        assert code["is_active"] is True

    def test_code_string_is_8_chars_uppercase(
        self, invite_api_client: TestClient
    ) -> None:
        resp = _create_invite_codes(invite_api_client, count=5)
        assert resp.status_code == 201
        for entry in resp.json()["codes"]:
            assert len(entry["code"]) == 8
            assert (
                entry["code"].isupper()
                or entry["code"].isdigit()
                or entry["code"].isalnum()
            )

    def test_returns_403_without_secret(self, invite_api_client: TestClient) -> None:
        resp = invite_api_client.post(
            "/admin/invite-codes",
            json={"count": 1},
        )
        assert resp.status_code == 403

    def test_returns_403_with_wrong_secret(self, invite_api_client: TestClient) -> None:
        resp = _create_invite_codes(invite_api_client, count=1, secret="wrong-secret")
        assert resp.status_code == 403

    def test_returns_422_when_count_exceeds_500(
        self, invite_api_client: TestClient
    ) -> None:
        resp = _create_invite_codes(invite_api_client, count=501)
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Tests: POST /auth/register (now requires invite_code)
# ---------------------------------------------------------------------------


class TestRegisterWithInvite:
    def test_register_succeeds_with_valid_invite(
        self, invite_api_client: TestClient
    ) -> None:
        # First create a code
        create_resp = _create_invite_codes(invite_api_client, count=1)
        assert create_resp.status_code == 201
        code = create_resp.json()["codes"][0]["code"]

        resp = _register_with_invite(invite_api_client, invite_code=code)
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert "user_id" in data
        assert data["email"] == "newuser@example.com"

    def test_register_fails_with_invalid_invite(
        self, invite_api_client: TestClient
    ) -> None:
        resp = _register_with_invite(invite_api_client, invite_code="BADCODE1")
        assert resp.status_code == 422
        assert "invalid" in resp.json()["detail"].lower()

    def test_invite_code_is_single_use(self, invite_api_client: TestClient) -> None:
        create_resp = _create_invite_codes(invite_api_client, count=1)
        code = create_resp.json()["codes"][0]["code"]

        # First registration succeeds
        resp1 = _register_with_invite(
            invite_api_client, invite_code=code, email="first@example.com"
        )
        assert resp1.status_code == 201

        # Second registration with same code fails
        resp2 = _register_with_invite(
            invite_api_client, invite_code=code, email="second@example.com"
        )
        assert resp2.status_code == 422

    def test_register_without_invite_code_returns_422(
        self, invite_api_client: TestClient
    ) -> None:
        resp = invite_api_client.post(
            "/auth/register",
            json={
                "email": "noinvite@example.com",
                "password": "StrongPass123!",
                "display_name": "No Invite",
            },
        )
        assert resp.status_code == 422

    def test_register_normalizes_invite_code_case(
        self, invite_api_client: TestClient
    ) -> None:
        create_resp = _create_invite_codes(invite_api_client, count=1)
        code = create_resp.json()["codes"][0]["code"]

        resp = _register_with_invite(
            invite_api_client,
            invite_code=code.lower(),
            email="casetest@example.com",
        )
        assert resp.status_code == 201
