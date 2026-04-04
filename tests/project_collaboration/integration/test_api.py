"""API integration tests: test FastAPI endpoints against real PostgreSQL.

Uses ``httpx`` sync TestClient + the test database (port 5433).
Each test runs inside a rolled-back transaction for isolation.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Connection, Engine, event
from sqlalchemy.orm import Session, sessionmaker

from project_collaboration.api.app import create_app
from project_collaboration.api.dependencies import get_uow
from project_collaboration.infrastructure.database import (
    TEST_DATABASE_URL,
    create_tables,
    drop_tables,
    get_engine,
)
from project_collaboration.infrastructure.sqlalchemy_unit_of_work import (
    SqlAlchemyUnitOfWork,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def api_engine() -> Engine:
    engine = get_engine(TEST_DATABASE_URL)
    drop_tables(engine)
    create_tables(engine)
    yield engine
    drop_tables(engine)
    engine.dispose()


@pytest.fixture()
def api_client(api_engine: Engine):
    """Create a TestClient whose UoW is bound to a rolled-back transaction.

    A single session is shared across all requests within one test.
    ``session.close()`` is replaced with ``session.expire_all()`` so the
    UoW ``__exit__`` (which calls close) does not terminate the session.
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
    # from destroying the shared session.  Both become no-ops; the real
    # cleanup happens in fixture teardown below.
    _real_close = session.close
    session.close = lambda: None  # type: ignore[assignment]
    session.rollback = lambda: None  # type: ignore[assignment]

    class _TestSessionFactory:
        """Always returns the same shared session."""

        def __call__(self) -> Session:
            return session

    factory = _TestSessionFactory()

    app = create_app()

    def _test_uow():
        uow = SqlAlchemyUnitOfWork(factory)  # type: ignore[arg-type]
        yield uow

    app.dependency_overrides[get_uow] = _test_uow

    client = TestClient(app)
    yield client

    _real_close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()


OWNER = "owner1"
HEADERS = {"X-Caller-Id": OWNER}


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _create_project(client: TestClient, **overrides) -> dict:
    """Create a project and return the response JSON."""
    body = {
        "project_id": "p1",
        "title": "Test Project",
        "description": "A test project description.",
        "required_skills": ["python"],
        "max_members": None,
    }
    body.update(overrides)
    resp = client.post("/projects", json=body, headers=HEADERS)
    assert resp.status_code == 201, resp.text
    return resp.json()


def _publish_project(client: TestClient, project_id: str = "p1") -> None:
    resp = client.post(f"/projects/{project_id}/publish", headers=HEADERS)
    assert resp.status_code == 200, resp.text


# ---------------------------------------------------------------------------
# Tests: Create Project
# ---------------------------------------------------------------------------


class TestCreateProject:
    def test_create_project_returns_201(self, api_client: TestClient) -> None:
        data = _create_project(api_client)
        assert data["project_id"] == "p1"
        assert data["title"] == "Test Project"
        assert data["owner_id"] == OWNER
        assert data["status"] == "draft"
        assert len(data["memberships"]) == 1
        assert data["memberships"][0]["role"] == "owner"

    def test_create_project_without_caller_id_returns_422(
        self, api_client: TestClient
    ) -> None:
        resp = api_client.post(
            "/projects",
            json={"project_id": "p1", "title": "Test Project"},
            # no X-Caller-Id header
        )
        assert resp.status_code == 422

    def test_create_project_with_short_title_returns_422(
        self, api_client: TestClient
    ) -> None:
        resp = api_client.post(
            "/projects",
            json={"project_id": "p1", "title": "ab"},
            headers=HEADERS,
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Tests: Get Project
# ---------------------------------------------------------------------------


class TestGetProject:
    def test_get_existing_project(self, api_client: TestClient) -> None:
        _create_project(api_client)
        resp = api_client.get("/projects/p1")
        assert resp.status_code == 200
        assert resp.json()["project_id"] == "p1"

    def test_get_nonexistent_project_returns_404(self, api_client: TestClient) -> None:
        resp = api_client.get("/projects/nonexistent")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Tests: Publish Project
# ---------------------------------------------------------------------------


class TestPublishProject:
    def test_publish_project(self, api_client: TestClient) -> None:
        _create_project(api_client)
        resp = api_client.post("/projects/p1/publish", headers=HEADERS)
        assert resp.status_code == 200

        project = api_client.get("/projects/p1").json()
        assert project["status"] == "recruiting"

    def test_publish_nonexistent_project_returns_404(
        self, api_client: TestClient
    ) -> None:
        resp = api_client.post("/projects/nonexistent/publish", headers=HEADERS)
        assert resp.status_code == 404

    def test_publish_by_non_owner_returns_403(self, api_client: TestClient) -> None:
        _create_project(api_client)
        resp = api_client.post(
            "/projects/p1/publish", headers={"X-Caller-Id": "stranger"}
        )
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Tests: Apply to Project
# ---------------------------------------------------------------------------


class TestApplyToProject:
    def test_apply_to_project(self, api_client: TestClient) -> None:
        _create_project(api_client)
        _publish_project(api_client)
        resp = api_client.post(
            "/projects/p1/applications",
            json={
                "application_id": "a1",
                "desired_role": "member",
                "motivation": "I want to join.",
                "applicant_skills": ["python"],
            },
            headers={"X-Caller-Id": "u2"},
        )
        assert resp.status_code == 201

    def test_apply_to_non_recruiting_project_returns_422(
        self, api_client: TestClient
    ) -> None:
        _create_project(api_client)
        # project is still Draft, not Recruiting
        resp = api_client.post(
            "/projects/p1/applications",
            json={
                "application_id": "a1",
                "desired_role": "member",
                "motivation": "I want to join.",
                "applicant_skills": [],
            },
            headers={"X-Caller-Id": "u2"},
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Tests: Accept/Reject Application
# ---------------------------------------------------------------------------


class TestReviewApplication:
    def test_accept_application(self, api_client: TestClient) -> None:
        _create_project(api_client)
        _publish_project(api_client)
        api_client.post(
            "/projects/p1/applications",
            json={
                "application_id": "a1",
                "desired_role": "member",
                "motivation": "I want to join.",
                "applicant_skills": ["python"],
            },
            headers={"X-Caller-Id": "u2"},
        )
        resp = api_client.post("/projects/p1/applications/a1/accept", headers=HEADERS)
        assert resp.status_code == 200

        project = api_client.get("/projects/p1").json()
        app = [a for a in project["applications"] if a["application_id"] == "a1"][0]
        assert app["status"] == "accepted"
        # New membership for u2
        u2_members = [m for m in project["memberships"] if m["user_id"] == "u2"]
        assert len(u2_members) == 1

    def test_reject_application(self, api_client: TestClient) -> None:
        _create_project(api_client)
        _publish_project(api_client)
        api_client.post(
            "/projects/p1/applications",
            json={
                "application_id": "a1",
                "desired_role": "member",
                "motivation": "I want to join.",
                "applicant_skills": ["python"],
            },
            headers={"X-Caller-Id": "u2"},
        )
        resp = api_client.post("/projects/p1/applications/a1/reject", headers=HEADERS)
        assert resp.status_code == 200

        project = api_client.get("/projects/p1").json()
        app = [a for a in project["applications"] if a["application_id"] == "a1"][0]
        assert app["status"] == "rejected"


# ---------------------------------------------------------------------------
# Tests: Member Management
# ---------------------------------------------------------------------------


class TestMemberManagement:
    def _create_project_with_member(self, client: TestClient) -> str:
        """Create project, publish, apply as u2, accept, return membership_id."""
        _create_project(client)
        _publish_project(client)
        client.post(
            "/projects/p1/applications",
            json={
                "application_id": "a1",
                "desired_role": "member",
                "motivation": "I want to join.",
                "applicant_skills": ["python"],
            },
            headers={"X-Caller-Id": "u2"},
        )
        client.post("/projects/p1/applications/a1/accept", headers=HEADERS)
        project = client.get("/projects/p1").json()
        u2_m = [m for m in project["memberships"] if m["user_id"] == "u2"][0]
        return u2_m["membership_id"]

    def test_change_member_role(self, api_client: TestClient) -> None:
        mid = self._create_project_with_member(api_client)
        resp = api_client.patch(
            f"/projects/p1/members/{mid}/role",
            json={"new_role": "admin"},
            headers=HEADERS,
        )
        assert resp.status_code == 200

        project = api_client.get("/projects/p1").json()
        u2_m = [m for m in project["memberships"] if m["user_id"] == "u2"][0]
        assert u2_m["role"] == "admin"

    def test_remove_member(self, api_client: TestClient) -> None:
        mid = self._create_project_with_member(api_client)
        resp = api_client.delete(f"/projects/p1/members/{mid}", headers=HEADERS)
        assert resp.status_code == 200

        project = api_client.get("/projects/p1").json()
        u2_m = [m for m in project["memberships"] if m["user_id"] == "u2"][0]
        assert u2_m["is_active"] is False


# ---------------------------------------------------------------------------
# Tests: Status Transitions
# ---------------------------------------------------------------------------


class TestStatusTransitions:
    def test_activate_project(self, api_client: TestClient) -> None:
        _create_project(api_client)
        _publish_project(api_client)
        resp = api_client.post("/projects/p1/activate", headers=HEADERS)
        assert resp.status_code == 200
        assert api_client.get("/projects/p1").json()["status"] == "active"

    def test_suspend_and_resume(self, api_client: TestClient) -> None:
        _create_project(api_client)
        _publish_project(api_client)
        api_client.post("/projects/p1/activate", headers=HEADERS)

        resp = api_client.post("/projects/p1/suspend", headers=HEADERS)
        assert resp.status_code == 200
        assert api_client.get("/projects/p1").json()["status"] == "suspended"

        resp = api_client.post("/projects/p1/resume", headers=HEADERS)
        assert resp.status_code == 200
        assert api_client.get("/projects/p1").json()["status"] == "active"

    def test_complete_project(self, api_client: TestClient) -> None:
        _create_project(api_client)
        _publish_project(api_client)
        api_client.post("/projects/p1/activate", headers=HEADERS)

        resp = api_client.post("/projects/p1/complete", headers=HEADERS)
        assert resp.status_code == 200
        assert api_client.get("/projects/p1").json()["status"] == "completed"

    def test_cancel_project(self, api_client: TestClient) -> None:
        _create_project(api_client)
        _publish_project(api_client)

        resp = api_client.post("/projects/p1/cancel", headers=HEADERS)
        assert resp.status_code == 200
        assert api_client.get("/projects/p1").json()["status"] == "cancelled"


# ---------------------------------------------------------------------------
# Tests: Search
# ---------------------------------------------------------------------------


class TestSearchProjects:
    def test_search_returns_projects(self, api_client: TestClient) -> None:
        _create_project(api_client, project_id="p1", title="Alpha Project")
        _create_project(api_client, project_id="p2", title="Beta Project")

        resp = api_client.get("/projects/search")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2

    def test_search_by_keyword(self, api_client: TestClient) -> None:
        _create_project(api_client, project_id="p1", title="Machine Learning")
        _create_project(api_client, project_id="p2", title="Web App")

        resp = api_client.get("/projects/search", params={"keyword": "machine"})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["project_id"] == "p1"

    def test_search_by_skills(self, api_client: TestClient) -> None:
        _create_project(
            api_client,
            project_id="p1",
            title="Python Project",
            required_skills=["python"],
        )
        _create_project(
            api_client,
            project_id="p2",
            title="Rust Project",
            required_skills=["rust"],
        )

        resp = api_client.get("/projects/search", params={"skills": "python"})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["project_id"] == "p1"


# ---------------------------------------------------------------------------
# Tests: Error Handling
# ---------------------------------------------------------------------------


class TestErrorHandling:
    def test_lookup_error_returns_404(self, api_client: TestClient) -> None:
        resp = api_client.get("/projects/nonexistent")
        assert resp.status_code == 404
        assert "detail" in resp.json()

    def test_permission_error_returns_403(self, api_client: TestClient) -> None:
        _create_project(api_client)
        resp = api_client.post(
            "/projects/p1/publish", headers={"X-Caller-Id": "stranger"}
        )
        assert resp.status_code == 403
        assert "detail" in resp.json()

    def test_value_error_returns_422(self, api_client: TestClient) -> None:
        _create_project(api_client)
        # Try to publish a Draft project, then activate (can't activate from draft)
        resp = api_client.post("/projects/p1/activate", headers=HEADERS)
        assert resp.status_code == 422
        assert "detail" in resp.json()
