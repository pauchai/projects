"""API integration tests for Feature Request endpoints.

Uses ``httpx`` sync TestClient + the test database (port 5433).
Each test runs inside a rolled-back transaction for isolation.

Covers:
- POST /features  (create feature request, auth required)
- GET  /features  (list all, with optional status/author_id filters)
- GET  /features/{id}  (get by ID, 404 for nonexistent)
- PUT  /admin/features/{id}/status  (status transition, auth required)
- Error handling (401, 404, 422)
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, event
from sqlalchemy.orm import Session

from auth.api.dependencies import get_auth_uow, get_password_hasher, get_token_service
from auth.infrastructure.jwt_token_service import JwtTokenService
from project_collaboration.api.app import create_app
from project_collaboration.api.dependencies import get_uow
from project_collaboration.infrastructure.database import (
    TEST_DATABASE_URL,
    get_engine,
)
from project_collaboration.infrastructure.sqlalchemy_unit_of_work import (
    SqlAlchemyUnitOfWork,
)
from shared_kernel.migration import run_migrations


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------

TEST_JWT_SECRET = "test-secret-for-feature-requests"
_test_token_service = JwtTokenService(
    secret=TEST_JWT_SECRET, algorithm="HS256", expire_minutes=60
)


def _auth_headers(user_id: str) -> dict[str, str]:
    """Create Authorization headers with a valid JWT for the given user_id."""
    token = _test_token_service.create_access_token(user_id)
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def feature_api_engine() -> Engine:
    engine = get_engine(TEST_DATABASE_URL)
    run_migrations(engine)
    yield engine
    engine.dispose()


@pytest.fixture()
def api_client(feature_api_engine: Engine):
    """Create a TestClient whose UoW is bound to a rolled-back transaction."""
    connection = feature_api_engine.connect()
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
    app = create_app()

    def _test_uow():
        uow = SqlAlchemyUnitOfWork(factory)  # type: ignore[arg-type]
        yield uow

    app.dependency_overrides[get_uow] = _test_uow
    app.dependency_overrides[get_token_service] = lambda: _test_token_service

    def _noop_auth_uow():
        yield None

    app.dependency_overrides[get_auth_uow] = _noop_auth_uow
    app.dependency_overrides[get_password_hasher] = lambda: None

    client = TestClient(app)
    yield client

    _real_close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()


USER1 = "user1"
USER1_HEADERS = _auth_headers(USER1)
USER2 = "user2"
USER2_HEADERS = _auth_headers(USER2)
ADMIN = "admin1"
ADMIN_HEADERS = _auth_headers(ADMIN)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _create_feature_request(
    client: TestClient, headers: dict | None = None, **overrides
) -> dict:
    """Create a feature request and return the response JSON."""
    body = {
        "request_id": "fr1",
        "title": "Dark mode support",
        "description": "Add a dark mode toggle to the application settings.",
    }
    body.update(overrides)
    resp = client.post("/features", json=body, headers=headers or USER1_HEADERS)
    assert resp.status_code == 201, resp.text
    return resp.json()


# ---------------------------------------------------------------------------
# Tests: Create Feature Request
# ---------------------------------------------------------------------------


class TestCreateFeatureRequest:
    def test_create_returns_201(self, api_client: TestClient) -> None:
        data = _create_feature_request(api_client)
        assert data["request_id"] == "fr1"
        assert data["title"] == "Dark mode support"
        assert data["author_id"] == USER1
        assert data["status"] == "submitted"
        assert data["category"] is None
        assert data["priority"] is None
        assert data["admin_notes"] == ""

    def test_create_with_category_and_priority(self, api_client: TestClient) -> None:
        data = _create_feature_request(
            api_client,
            request_id="fr2",
            category="ui",
            priority="high",
        )
        assert data["category"] == "ui"
        assert data["priority"] == "high"

    def test_create_without_token_returns_401(self, api_client: TestClient) -> None:
        resp = api_client.post(
            "/features",
            json={
                "request_id": "fr1",
                "title": "Dark mode support",
                "description": "A description.",
            },
        )
        assert resp.status_code == 401

    def test_create_with_invalid_token_returns_401(
        self, api_client: TestClient
    ) -> None:
        resp = api_client.post(
            "/features",
            json={
                "request_id": "fr1",
                "title": "Dark mode support",
                "description": "A description.",
            },
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert resp.status_code == 401

    def test_create_with_short_title_returns_422(self, api_client: TestClient) -> None:
        resp = api_client.post(
            "/features",
            json={
                "request_id": "fr1",
                "title": "ab",
                "description": "A description.",
            },
            headers=USER1_HEADERS,
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Tests: Get Feature Request
# ---------------------------------------------------------------------------


class TestGetFeatureRequest:
    def test_get_existing_feature_request(self, api_client: TestClient) -> None:
        _create_feature_request(api_client)
        resp = api_client.get("/features/fr1")
        assert resp.status_code == 200
        assert resp.json()["request_id"] == "fr1"
        assert resp.json()["title"] == "Dark mode support"

    def test_get_nonexistent_returns_404(self, api_client: TestClient) -> None:
        resp = api_client.get("/features/nonexistent")
        assert resp.status_code == 404
        assert "detail" in resp.json()


# ---------------------------------------------------------------------------
# Tests: List Feature Requests
# ---------------------------------------------------------------------------


class TestListFeatureRequests:
    def test_list_returns_all(self, api_client: TestClient) -> None:
        _create_feature_request(api_client, request_id="fr1", title="Feature One")
        _create_feature_request(api_client, request_id="fr2", title="Feature Two")

        resp = api_client.get("/features")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2

    def test_list_filter_by_status(self, api_client: TestClient) -> None:
        _create_feature_request(api_client, request_id="fr1", title="Submitted One")
        _create_feature_request(api_client, request_id="fr2", title="To Be Planned")
        # Transition fr2 to planned
        api_client.put(
            "/admin/features/fr2/status",
            json={"status": "planned"},
            headers=ADMIN_HEADERS,
        )

        resp = api_client.get("/features", params={"status": "planned"})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["request_id"] == "fr2"

    def test_list_filter_by_author_id(self, api_client: TestClient) -> None:
        _create_feature_request(
            api_client, request_id="fr1", title="User1 Feat", headers=USER1_HEADERS
        )
        _create_feature_request(
            api_client, request_id="fr2", title="User2 Feat", headers=USER2_HEADERS
        )

        resp = api_client.get("/features", params={"author_id": USER1})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["author_id"] == USER1


# ---------------------------------------------------------------------------
# Tests: Update Feature Status (admin)
# ---------------------------------------------------------------------------


class TestUpdateFeatureStatus:
    def test_transition_to_planned(self, api_client: TestClient) -> None:
        _create_feature_request(api_client)
        resp = api_client.put(
            "/admin/features/fr1/status",
            json={"status": "planned"},
            headers=ADMIN_HEADERS,
        )
        assert resp.status_code == 200
        assert "planned" in resp.json()["message"]

        # Verify the status was updated
        detail = api_client.get("/features/fr1").json()
        assert detail["status"] == "planned"

    def test_transition_with_admin_notes(self, api_client: TestClient) -> None:
        _create_feature_request(api_client)
        resp = api_client.put(
            "/admin/features/fr1/status",
            json={"status": "planned", "admin_notes": "Scheduled for Q3"},
            headers=ADMIN_HEADERS,
        )
        assert resp.status_code == 200

        detail = api_client.get("/features/fr1").json()
        assert detail["status"] == "planned"
        assert detail["admin_notes"] == "Scheduled for Q3"

    def test_full_lifecycle_submitted_to_done(self, api_client: TestClient) -> None:
        _create_feature_request(api_client)

        # submitted → planned
        resp = api_client.put(
            "/admin/features/fr1/status",
            json={"status": "planned"},
            headers=ADMIN_HEADERS,
        )
        assert resp.status_code == 200

        # planned → in_progress
        resp = api_client.put(
            "/admin/features/fr1/status",
            json={"status": "in_progress"},
            headers=ADMIN_HEADERS,
        )
        assert resp.status_code == 200

        # in_progress → done
        resp = api_client.put(
            "/admin/features/fr1/status",
            json={"status": "done"},
            headers=ADMIN_HEADERS,
        )
        assert resp.status_code == 200

        detail = api_client.get("/features/fr1").json()
        assert detail["status"] == "done"

    def test_reject_feature_request(self, api_client: TestClient) -> None:
        _create_feature_request(api_client)
        resp = api_client.put(
            "/admin/features/fr1/status",
            json={"status": "rejected", "admin_notes": "Not aligned with roadmap"},
            headers=ADMIN_HEADERS,
        )
        assert resp.status_code == 200

        detail = api_client.get("/features/fr1").json()
        assert detail["status"] == "rejected"
        assert detail["admin_notes"] == "Not aligned with roadmap"

    def test_invalid_transition_returns_422(self, api_client: TestClient) -> None:
        _create_feature_request(api_client)
        # submitted → done is not allowed
        resp = api_client.put(
            "/admin/features/fr1/status",
            json={"status": "done"},
            headers=ADMIN_HEADERS,
        )
        assert resp.status_code == 422
        assert "detail" in resp.json()

    def test_nonexistent_request_returns_404(self, api_client: TestClient) -> None:
        resp = api_client.put(
            "/admin/features/nonexistent/status",
            json={"status": "planned"},
            headers=ADMIN_HEADERS,
        )
        assert resp.status_code == 404

    def test_update_status_without_token_returns_401(
        self, api_client: TestClient
    ) -> None:
        _create_feature_request(api_client)
        resp = api_client.put(
            "/admin/features/fr1/status",
            json={"status": "planned"},
        )
        assert resp.status_code == 401
