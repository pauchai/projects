"""Integration tests for PATCH /auth/me endpoint.

Tests the full HTTP → route → use case → repository flow with a real
PostgreSQL database.
"""

from __future__ import annotations

import uuid

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

JWT_SECRET = "test-update-profile-secret-32c!"


@pytest.fixture(scope="module")
def update_profile_engine() -> Engine:
    engine = get_engine(TEST_DATABASE_URL)
    run_migrations(engine)
    yield engine
    engine.dispose()


@pytest.fixture()
def update_profile_client(update_profile_engine: Engine):
    """TestClient with SAVEPOINT isolation."""
    connection = update_profile_engine.connect()
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
    yield client, session, factory, token_service

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


def _create_telegram_user_and_get_token(
    session: Session,
    factory,
    token_service: JwtTokenService,
    telegram_id: str = "99999999",
) -> tuple[str, str]:
    """Insert a Telegram-only user with synthetic email, return (user_id, token)."""
    user_id = str(uuid.uuid4())
    synthetic_email = f"{telegram_id}@telegram.user"
    uow = SqlAlchemyUnitOfWork(factory)  # type: ignore[arg-type]
    with uow:
        user = User(
            user_id=user_id, email=synthetic_email, display_name="Telegram User"
        )
        tg_cred = Credential(
            credential_id=str(uuid.uuid4()),
            user_id=user_id,
            provider="telegram",
            provider_user_id=telegram_id,
            hashed_secret=None,
        )
        user.add_credential(tg_cred)
        uow.users.save(user)
        uow.commit()
    return user_id, token_service.create_access_token(user_id)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestUpdateProfile:
    """PATCH /auth/me"""

    def test_update_email_returns_new_email_in_response(
        self, update_profile_client
    ) -> None:
        client, _, __, ___ = update_profile_client
        uid = str(uuid.uuid4())[:8]
        _, token = _register_and_get_token(client, email=f"up-email-{uid}@example.com")

        resp = client.patch(
            "/auth/me",
            json={"email": f"up-updated-{uid}@example.com"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["email"] == f"up-updated-{uid}@example.com"

    def test_update_display_name_returns_new_name_in_response(
        self, update_profile_client
    ) -> None:
        client, _, __, ___ = update_profile_client
        uid = str(uuid.uuid4())[:8]
        _, token = _register_and_get_token(
            client,
            email=f"up-name-{uid}@example.com",
            display_name="Old Name",
        )

        resp = client.patch(
            "/auth/me",
            json={"display_name": "New Name"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["display_name"] == "New Name"

    def test_update_with_no_fields_is_noop(self, update_profile_client) -> None:
        client, _, __, ___ = update_profile_client
        uid = str(uuid.uuid4())[:8]
        user_data, token = _register_and_get_token(
            client,
            email=f"up-noop-{uid}@example.com",
            display_name="Unchanged",
        )

        resp = client.patch(
            "/auth/me",
            json={},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["email"] == f"up-noop-{uid}@example.com"
        assert data["display_name"] == "Unchanged"

    def test_get_me_reflects_updated_email(self, update_profile_client) -> None:
        """After PATCH, GET /auth/me returns the new email."""
        client, _, __, ___ = update_profile_client
        uid = str(uuid.uuid4())[:8]
        _, token = _register_and_get_token(
            client, email=f"up-reflect-{uid}@example.com"
        )

        client.patch(
            "/auth/me",
            json={"email": f"up-reflected-{uid}@example.com"},
            headers={"Authorization": f"Bearer {token}"},
        )

        resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()["email"] == f"up-reflected-{uid}@example.com"

    def test_returns_422_when_email_already_taken(self, update_profile_client) -> None:
        client, _, __, ___ = update_profile_client
        uid = str(uuid.uuid4())[:8]
        _register_and_get_token(client, email=f"up-taken-{uid}@example.com")
        _, token2 = _register_and_get_token(client, email=f"up-other-{uid}@example.com")

        resp = client.patch(
            "/auth/me",
            json={"email": f"up-taken-{uid}@example.com"},
            headers={"Authorization": f"Bearer {token2}"},
        )
        assert resp.status_code == 422
        assert "Email already registered" in resp.json()["detail"]

    def test_requires_authentication(self, update_profile_client) -> None:
        client, _, __, ___ = update_profile_client
        resp = client.patch("/auth/me", json={"display_name": "Hacker"})
        assert resp.status_code == 401

    def test_synthetic_telegram_email_can_be_replaced(
        self, update_profile_client
    ) -> None:
        """Key scenario: Telegram user sets a real email via PATCH /auth/me."""
        client, session, factory, token_service = update_profile_client
        uid = str(uuid.uuid4())[:8]
        _, token = _create_telegram_user_and_get_token(
            session, factory, token_service, telegram_id=f"tg{uid}"
        )

        resp = client.patch(
            "/auth/me",
            json={"email": f"real-{uid}@example.com"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["email"] == f"real-{uid}@example.com"
