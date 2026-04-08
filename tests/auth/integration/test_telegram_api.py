"""Telegram OAuth API integration tests: test Telegram endpoints against real PostgreSQL.

Uses ``httpx`` sync TestClient + test database (port 5433).
Tests the full HTTP -> route -> use case -> repository flow.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, event
from sqlalchemy.orm import Session

from auth.api.app import create_auth_app
from auth.api.dependencies import (
    get_auth_uow,
    get_password_hasher,
    get_telegram_oauth_client,
    get_token_service,
)
from auth.infrastructure.bcrypt_password_hasher import BcryptPasswordHasher
from auth.infrastructure.database import (
    TEST_DATABASE_URL,
    create_tables,
    drop_tables,
    get_engine,
)
from auth.infrastructure.jwt_token_service import JwtTokenService
from auth.infrastructure.providers.telegram_oauth_client import TelegramOAuthClient
from auth.infrastructure.sqlalchemy_unit_of_work import SqlAlchemyUnitOfWork


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

JWT_SECRET = "test-secret-telegram"


@pytest.fixture(scope="module")
def telegram_api_engine() -> Engine:
    engine = get_engine(TEST_DATABASE_URL)
    drop_tables(engine)
    create_tables(engine)
    yield engine
    drop_tables(engine)
    engine.dispose()


@pytest.fixture()
def telegram_api_client(telegram_api_engine: Engine):
    """TestClient with real TelegramOAuthClient for Telegram endpoints."""
    connection = telegram_api_engine.connect()
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
    telegram_client = TelegramOAuthClient(bot_username="test_bot")

    app.dependency_overrides[get_auth_uow] = _test_uow
    app.dependency_overrides[get_password_hasher] = lambda: password_hasher
    app.dependency_overrides[get_token_service] = lambda: token_service
    app.dependency_overrides[get_telegram_oauth_client] = lambda: telegram_client

    client = TestClient(app)
    yield client

    _real_close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()


@pytest.fixture()
def telegram_unavailable_client(telegram_api_engine: Engine):
    """TestClient where Telegram OAuth is NOT configured (returns None)."""
    app = create_auth_app()
    app.dependency_overrides[get_telegram_oauth_client] = lambda: None

    client = TestClient(app)
    yield client


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _do_full_telegram_flow(client: TestClient) -> dict:
    """Perform the complete Telegram auth flow and return the callback response.

    1. GET /authorize -> get telegram_url + state
    2. POST /bot-callback -> simulate bot sending user data
    3. POST /callback -> exchange code + state for JWT
    """
    # Step 1: Authorize
    auth_resp = client.get("/auth/oauth/telegram/authorize")
    assert auth_resp.status_code == 200
    auth_data = auth_resp.json()
    telegram_url = auth_data["telegram_url"]
    state = auth_data["state"]

    # Extract auth_code from the telegram URL (format: https://t.me/bot?start=<auth_code>)
    auth_code = telegram_url.split("start=")[1]

    # Step 2: Bot callback
    bot_resp = client.post(
        "/auth/oauth/telegram/bot-callback",
        json={
            "auth_code": auth_code,
            "telegram_user_id": "12345",
            "telegram_username": "john_doe",
            "telegram_first_name": "John",
        },
    )
    assert bot_resp.status_code == 200
    bot_data = bot_resp.json()
    authorization_code = bot_data["authorization_code"]

    # Step 3: Callback
    callback_resp = client.post(
        "/auth/oauth/telegram/callback",
        json={"code": authorization_code, "state": state},
    )
    return callback_resp.json(), callback_resp.status_code


# ---------------------------------------------------------------------------
# Tests: GET /auth/oauth/telegram/available
# ---------------------------------------------------------------------------


class TestTelegramOAuthAvailable:
    def test_returns_available_true_when_configured(
        self, telegram_api_client: TestClient
    ) -> None:
        resp = telegram_api_client.get("/auth/oauth/telegram/available")
        assert resp.status_code == 200
        assert resp.json()["available"] is True

    def test_returns_available_false_when_not_configured(
        self, telegram_unavailable_client: TestClient
    ) -> None:
        resp = telegram_unavailable_client.get("/auth/oauth/telegram/available")
        assert resp.status_code == 200
        assert resp.json()["available"] is False


# ---------------------------------------------------------------------------
# Tests: GET /auth/oauth/telegram/authorize
# ---------------------------------------------------------------------------


class TestTelegramOAuthAuthorize:
    def test_returns_telegram_url_and_state(
        self, telegram_api_client: TestClient
    ) -> None:
        resp = telegram_api_client.get("/auth/oauth/telegram/authorize")
        assert resp.status_code == 200
        data = resp.json()
        assert "telegram_url" in data
        assert "state" in data
        assert "t.me/test_bot" in data["telegram_url"]
        assert "start=" in data["telegram_url"]
        assert len(data["state"]) > 0

    def test_returns_501_when_not_configured(
        self, telegram_unavailable_client: TestClient
    ) -> None:
        resp = telegram_unavailable_client.get("/auth/oauth/telegram/authorize")
        assert resp.status_code == 501
        assert "not configured" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Tests: POST /auth/oauth/telegram/bot-callback
# ---------------------------------------------------------------------------


class TestTelegramBotCallback:
    def test_returns_authorization_code_and_state(
        self, telegram_api_client: TestClient
    ) -> None:
        # First create an auth request
        auth_resp = telegram_api_client.get("/auth/oauth/telegram/authorize")
        auth_data = auth_resp.json()
        auth_code = auth_data["telegram_url"].split("start=")[1]
        state = auth_data["state"]

        # Simulate bot callback
        resp = telegram_api_client.post(
            "/auth/oauth/telegram/bot-callback",
            json={
                "auth_code": auth_code,
                "telegram_user_id": "12345",
                "telegram_username": "john_doe",
                "telegram_first_name": "John",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "authorization_code" in data
        assert data["state"] == state
        assert len(data["authorization_code"]) > 0

    def test_returns_404_for_unknown_auth_code(
        self, telegram_api_client: TestClient
    ) -> None:
        resp = telegram_api_client.post(
            "/auth/oauth/telegram/bot-callback",
            json={
                "auth_code": "nonexistent-code",
                "telegram_user_id": "12345",
                "telegram_username": "john_doe",
                "telegram_first_name": "John",
            },
        )
        assert resp.status_code == 404

    def test_returns_501_when_not_configured(
        self, telegram_unavailable_client: TestClient
    ) -> None:
        resp = telegram_unavailable_client.post(
            "/auth/oauth/telegram/bot-callback",
            json={
                "auth_code": "some-code",
                "telegram_user_id": "12345",
                "telegram_username": "john_doe",
                "telegram_first_name": "John",
            },
        )
        assert resp.status_code == 501


# ---------------------------------------------------------------------------
# Tests: POST /auth/oauth/telegram/callback
# ---------------------------------------------------------------------------


class TestTelegramOAuthCallback:
    def test_full_flow_creates_user_and_returns_token(
        self, telegram_api_client: TestClient
    ) -> None:
        data, status = _do_full_telegram_flow(telegram_api_client)
        assert status == 200
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0

    def test_full_flow_returns_valid_jwt(self, telegram_api_client: TestClient) -> None:
        data, status = _do_full_telegram_flow(telegram_api_client)
        assert status == 200

        token = data["access_token"]
        service = JwtTokenService(secret=JWT_SECRET)
        user_id = service.decode_token(token)
        assert len(user_id) > 0

    def test_callback_returns_400_for_invalid_code(
        self, telegram_api_client: TestClient
    ) -> None:
        resp = telegram_api_client.post(
            "/auth/oauth/telegram/callback",
            json={"code": "invalid-code", "state": "invalid-state"},
        )
        assert resp.status_code == 400

    def test_callback_returns_400_for_wrong_state(
        self, telegram_api_client: TestClient
    ) -> None:
        # Create auth request and do bot callback
        auth_resp = telegram_api_client.get("/auth/oauth/telegram/authorize")
        auth_data = auth_resp.json()
        auth_code = auth_data["telegram_url"].split("start=")[1]

        bot_resp = telegram_api_client.post(
            "/auth/oauth/telegram/bot-callback",
            json={
                "auth_code": auth_code,
                "telegram_user_id": "12345",
                "telegram_username": "john_doe",
                "telegram_first_name": "John",
            },
        )
        authorization_code = bot_resp.json()["authorization_code"]

        # Try callback with wrong state
        resp = telegram_api_client.post(
            "/auth/oauth/telegram/callback",
            json={"code": authorization_code, "state": "wrong-state"},
        )
        assert resp.status_code == 400
        assert "state mismatch" in resp.json()["detail"].lower()

    def test_callback_returns_501_when_not_configured(
        self, telegram_unavailable_client: TestClient
    ) -> None:
        resp = telegram_unavailable_client.post(
            "/auth/oauth/telegram/callback",
            json={"code": "some-code", "state": "some-state"},
        )
        assert resp.status_code == 501

    def test_callback_returns_422_for_missing_code(
        self, telegram_api_client: TestClient
    ) -> None:
        resp = telegram_api_client.post(
            "/auth/oauth/telegram/callback",
            json={"state": "random-state"},
        )
        assert resp.status_code == 422

    def test_callback_returns_422_for_empty_code(
        self, telegram_api_client: TestClient
    ) -> None:
        resp = telegram_api_client.post(
            "/auth/oauth/telegram/callback",
            json={"code": "", "state": "random-state"},
        )
        assert resp.status_code == 422
