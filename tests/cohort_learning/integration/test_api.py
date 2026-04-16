"""API integration tests for Cohort Learning endpoints.

Uses ``httpx`` sync TestClient + the test database (port 5433).
Each test runs inside a rolled-back transaction for isolation.

Authentication is handled via JWT Bearer tokens using a test JwtTokenService.
The ``get_token_service`` dependency is overridden with a fast test instance.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Connection, Engine, event
from sqlalchemy.orm import Session, sessionmaker

from auth.api.dependencies import get_auth_uow, get_password_hasher, get_token_service
from auth.infrastructure.jwt_token_service import JwtTokenService
from cohort_learning.api.dependencies import get_cohort_uow
from cohort_learning.infrastructure.sqlalchemy_unit_of_work import (
    SqlAlchemyUnitOfWork as CohortUnitOfWork,
)
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

TEST_JWT_SECRET = "test-secret-for-cohort-learning"
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
def api_engine() -> Engine:
    engine = get_engine(TEST_DATABASE_URL)
    run_migrations(engine)
    yield engine
    engine.dispose()


@pytest.fixture()
def api_client(api_engine: Engine):
    """Create a TestClient whose UoW is bound to a rolled-back transaction.

    A single session is shared across all requests within one test.
    ``session.close()`` is replaced with a no-op so the UoW ``__exit__``
    (which calls close) does not terminate the session.
    The real close happens in fixture teardown.
    """
    connection = api_engine.connect()
    transaction = connection.begin()

    session = Session(bind=connection)
    session.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(sess: Session, txn: object) -> None:
        if not sess.in_nested_transaction():
            sess.begin_nested()

    # Prevent UoW.__exit__ (which calls session.rollback() + session.close())
    # from destroying the shared session.
    _real_close = session.close
    session.close = lambda: None  # type: ignore[assignment]
    session.rollback = lambda: None  # type: ignore[assignment]

    class _TestSessionFactory:
        """Always returns the same shared session."""

        def __call__(self) -> Session:
            return session

    factory = _TestSessionFactory()

    app = create_app()

    # Override cohort learning UoW
    def _test_cohort_uow():
        uow = CohortUnitOfWork(factory)  # type: ignore[arg-type]
        yield uow

    app.dependency_overrides[get_cohort_uow] = _test_cohort_uow

    # Override project collaboration UoW (needed because app mounts both routers)
    def _test_uow():
        uow = SqlAlchemyUnitOfWork(factory)  # type: ignore[arg-type]
        yield uow

    app.dependency_overrides[get_uow] = _test_uow

    # Override token service (used by get_current_user_id dependency)
    app.dependency_overrides[get_token_service] = lambda: _test_token_service

    # Override auth-specific dependencies with no-ops
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


MASTER = "master1"
MASTER_HEADERS = _auth_headers(MASTER)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _form_cohort(
    client: TestClient,
    cohort_id: str = "c1",
    module_id: str = "mod1",
) -> dict:
    """Form a cohort and return the response JSON."""
    resp = client.post(
        "/cohorts",
        json={"cohort_id": cohort_id, "module_id": module_id},
        headers=MASTER_HEADERS,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _enrol_learners(
    client: TestClient,
    cohort_id: str = "c1",
    count: int = 5,
    start: int = 1,
) -> None:
    """Enrol `count` learners into a cohort (membership_id = m{i}, learner_id = l{i})."""
    for i in range(start, start + count):
        resp = client.post(
            f"/cohorts/{cohort_id}/learners",
            json={"membership_id": f"m{i}", "learner_id": f"l{i}"},
            headers=MASTER_HEADERS,
        )
        assert resp.status_code == 201, resp.text


# ---------------------------------------------------------------------------
# Tests: Form Cohort
# ---------------------------------------------------------------------------


class TestFormCohort:
    def test_form_cohort_returns_201(self, api_client: TestClient) -> None:
        data = _form_cohort(api_client)
        assert data["cohort_id"] == "c1"
        assert data["master_id"] == MASTER
        assert data["module_id"] == "mod1"
        assert data["status"] == "forming"
        assert data["memberships"] == []

    def test_form_cohort_without_token_returns_401(
        self, api_client: TestClient
    ) -> None:
        resp = api_client.post(
            "/cohorts",
            json={"cohort_id": "c1", "module_id": "mod1"},
        )
        assert resp.status_code == 401

    def test_form_cohort_with_invalid_token_returns_401(
        self, api_client: TestClient
    ) -> None:
        resp = api_client.post(
            "/cohorts",
            json={"cohort_id": "c1", "module_id": "mod1"},
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Tests: Get Cohort
# ---------------------------------------------------------------------------


class TestGetCohort:
    def test_get_existing_cohort(self, api_client: TestClient) -> None:
        _form_cohort(api_client)
        resp = api_client.get("/cohorts/c1")
        assert resp.status_code == 200
        assert resp.json()["cohort_id"] == "c1"

    def test_get_nonexistent_cohort_returns_404(self, api_client: TestClient) -> None:
        resp = api_client.get("/cohorts/nonexistent")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Tests: Enrol Learner
# ---------------------------------------------------------------------------


class TestEnrolLearner:
    def test_enrol_learner_returns_201(self, api_client: TestClient) -> None:
        _form_cohort(api_client)
        resp = api_client.post(
            "/cohorts/c1/learners",
            json={"membership_id": "m1", "learner_id": "l1"},
            headers=MASTER_HEADERS,
        )
        assert resp.status_code == 201
        assert resp.json()["message"] == "Learner enrolled"

        # Verify membership exists via GET
        cohort = api_client.get("/cohorts/c1").json()
        assert len(cohort["memberships"]) == 1
        assert cohort["memberships"][0]["learner_id"] == "l1"

    def test_enrol_by_non_master_returns_403(self, api_client: TestClient) -> None:
        _form_cohort(api_client)
        resp = api_client.post(
            "/cohorts/c1/learners",
            json={"membership_id": "m1", "learner_id": "l1"},
            headers=_auth_headers("stranger"),
        )
        assert resp.status_code == 403

    def test_enrol_master_as_learner_returns_422(self, api_client: TestClient) -> None:
        _form_cohort(api_client)
        resp = api_client.post(
            "/cohorts/c1/learners",
            json={"membership_id": "m1", "learner_id": MASTER},
            headers=MASTER_HEADERS,
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Tests: Remove Learner
# ---------------------------------------------------------------------------


class TestRemoveLearner:
    def test_remove_learner(self, api_client: TestClient) -> None:
        _form_cohort(api_client)
        _enrol_learners(api_client, count=1)

        resp = api_client.delete("/cohorts/c1/learners/m1", headers=MASTER_HEADERS)
        assert resp.status_code == 200
        assert resp.json()["message"] == "Learner removed"

        cohort = api_client.get("/cohorts/c1").json()
        m1 = [m for m in cohort["memberships"] if m["membership_id"] == "m1"][0]
        assert m1["is_active"] is False

    def test_remove_by_non_master_returns_403(self, api_client: TestClient) -> None:
        _form_cohort(api_client)
        _enrol_learners(api_client, count=1)

        resp = api_client.delete(
            "/cohorts/c1/learners/m1", headers=_auth_headers("stranger")
        )
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Tests: Status Transitions
# ---------------------------------------------------------------------------


class TestStatusTransitions:
    def test_activate_cohort(self, api_client: TestClient) -> None:
        _form_cohort(api_client)
        _enrol_learners(api_client, count=5)

        resp = api_client.post("/cohorts/c1/activate", headers=MASTER_HEADERS)
        assert resp.status_code == 200
        assert api_client.get("/cohorts/c1").json()["status"] == "active"

    def test_activate_without_min_learners_returns_422(
        self, api_client: TestClient
    ) -> None:
        _form_cohort(api_client)
        _enrol_learners(api_client, count=2)

        resp = api_client.post("/cohorts/c1/activate", headers=MASTER_HEADERS)
        assert resp.status_code == 422

    def test_begin_completing_cohort(self, api_client: TestClient) -> None:
        _form_cohort(api_client)
        _enrol_learners(api_client, count=5)
        api_client.post("/cohorts/c1/activate", headers=MASTER_HEADERS)

        resp = api_client.post("/cohorts/c1/begin-completing", headers=MASTER_HEADERS)
        assert resp.status_code == 200
        assert api_client.get("/cohorts/c1").json()["status"] == "completing"

    def test_graduate_cohort(self, api_client: TestClient) -> None:
        _form_cohort(api_client)
        _enrol_learners(api_client, count=5)
        api_client.post("/cohorts/c1/activate", headers=MASTER_HEADERS)
        api_client.post("/cohorts/c1/begin-completing", headers=MASTER_HEADERS)

        resp = api_client.post("/cohorts/c1/graduate", headers=MASTER_HEADERS)
        assert resp.status_code == 200
        assert api_client.get("/cohorts/c1").json()["status"] == "graduated"

    def test_cancel_cohort_from_forming(self, api_client: TestClient) -> None:
        _form_cohort(api_client)

        resp = api_client.post("/cohorts/c1/cancel", headers=MASTER_HEADERS)
        assert resp.status_code == 200
        assert api_client.get("/cohorts/c1").json()["status"] == "cancelled"

    def test_cancel_cohort_from_active(self, api_client: TestClient) -> None:
        _form_cohort(api_client)
        _enrol_learners(api_client, count=5)
        api_client.post("/cohorts/c1/activate", headers=MASTER_HEADERS)

        resp = api_client.post("/cohorts/c1/cancel", headers=MASTER_HEADERS)
        assert resp.status_code == 200
        assert api_client.get("/cohorts/c1").json()["status"] == "cancelled"

    def test_invalid_transition_returns_422(self, api_client: TestClient) -> None:
        _form_cohort(api_client)
        # Cannot begin-completing from forming (need active first)
        resp = api_client.post("/cohorts/c1/begin-completing", headers=MASTER_HEADERS)
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Tests: Error Handling
# ---------------------------------------------------------------------------


class TestErrorHandling:
    def test_missing_token_returns_401(self, api_client: TestClient) -> None:
        resp = api_client.post(
            "/cohorts",
            json={"cohort_id": "c1", "module_id": "mod1"},
        )
        assert resp.status_code == 401
        assert "detail" in resp.json()

    def test_invalid_token_returns_401(self, api_client: TestClient) -> None:
        resp = api_client.post(
            "/cohorts",
            json={"cohort_id": "c1", "module_id": "mod1"},
            headers={"Authorization": "Bearer garbage"},
        )
        assert resp.status_code == 401
        assert "detail" in resp.json()

    def test_lookup_error_returns_404(self, api_client: TestClient) -> None:
        resp = api_client.get("/cohorts/nonexistent")
        assert resp.status_code == 404
        assert "detail" in resp.json()

    def test_permission_error_returns_403(self, api_client: TestClient) -> None:
        _form_cohort(api_client)
        resp = api_client.post(
            "/cohorts/c1/learners",
            json={"membership_id": "m1", "learner_id": "l1"},
            headers=_auth_headers("stranger"),
        )
        assert resp.status_code == 403
        assert "detail" in resp.json()

    def test_value_error_returns_422(self, api_client: TestClient) -> None:
        _form_cohort(api_client)
        # Try to activate without enough learners
        resp = api_client.post("/cohorts/c1/activate", headers=MASTER_HEADERS)
        assert resp.status_code == 422
        assert "detail" in resp.json()
