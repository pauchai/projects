"""API integration tests for Pending Eligibility Notification endpoints.

Tests verify:
- GET /cohorts/{cohort_id}/pending-competency-validations
- GET /cohorts/{cohort_id}/pending-curator-promotions
- Authorization rules (Master/Curator for competency, Master-only for curator)
- Dynamic filtering of stale records
"""

from __future__ import annotations

from datetime import datetime, UTC

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Connection, Engine, event
from sqlalchemy.orm import Session

from auth.api.dependencies import get_auth_uow, get_password_hasher, get_token_service
from auth.infrastructure.jwt_token_service import JwtTokenService
from cohort_learning.api.dependencies import get_cohort_uow
from cohort_learning.domain.cohort_role import CohortRole
from cohort_learning.domain.pending_competency_validation import (
    PendingCompetencyValidation,
)
from cohort_learning.domain.pending_curator_promotion import PendingCuratorPromotion
from cohort_learning.infrastructure.sqlalchemy_unit_of_work import (
    SqlAlchemyUnitOfWork as CohortUnitOfWork,
)
from project_collaboration.api.app import create_app
from project_collaboration.infrastructure.database import (
    TEST_DATABASE_URL,
    get_engine,
)
from shared_kernel.migration import run_migrations
from tests.cohort_learning.factories import (
    create_cohort,
    create_module_curator,
    create_topic_expert,
)


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------

TEST_JWT_SECRET = "test-eligibility-secret"
_test_token_service = JwtTokenService(
    secret=TEST_JWT_SECRET, algorithm="HS256", expire_minutes=60
)


def _auth_headers(user_id: str) -> dict[str, str]:
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
    """TestClient whose UoW is bound to a rolled-back transaction."""
    connection = api_engine.connect()
    transaction = connection.begin()

    session = Session(bind=connection)
    session.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(sess: Session, txn: object) -> None:
        if not sess.in_nested_transaction():
            sess.begin_nested()

    original_close = session.close
    original_rollback = session.rollback

    session.close = lambda: None  # type: ignore[assignment]
    session.rollback = lambda: None  # type: ignore[assignment]

    class _TestSessionFactory:
        def __call__(self) -> Session:
            return session

    factory = _TestSessionFactory()

    app = create_app()

    def _cohort_uow_override():
        uow = CohortUnitOfWork(factory)  # type: ignore[arg-type]
        uow._session = session
        return uow

    app.dependency_overrides[get_cohort_uow] = _cohort_uow_override
    app.dependency_overrides[get_token_service] = lambda: _test_token_service

    def _noop_auth_uow():
        yield None

    app.dependency_overrides[get_auth_uow] = _noop_auth_uow
    app.dependency_overrides[get_password_hasher] = lambda: None

    client = TestClient(app)
    yield client

    transaction.rollback()
    session.close = original_close  # type: ignore[method-assign]
    session.rollback = original_rollback  # type: ignore[method-assign]
    session.close()
    connection.close()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_pending_competency(
    pending_id: str,
    learner_id: str,
    topic_id: str,
    cohort_id: str,
) -> PendingCompetencyValidation:
    return PendingCompetencyValidation(
        pending_id=pending_id,
        learner_id=learner_id,
        topic_id=topic_id,
        cohort_id=cohort_id,
        created_at=datetime.now(tz=UTC),
    )


def _make_pending_curator(
    pending_id: str,
    learner_id: str,
    module_id: str,
    cohort_id: str,
) -> PendingCuratorPromotion:
    return PendingCuratorPromotion(
        pending_id=pending_id,
        learner_id=learner_id,
        module_id=module_id,
        cohort_id=cohort_id,
        created_at=datetime.now(tz=UTC),
    )


# ---------------------------------------------------------------------------
# Tests: GET pending-competency-validations
# ---------------------------------------------------------------------------


class TestGetPendingCompetencyValidations:
    def test_master_gets_pending_validations(self, api_client: TestClient):
        """Master can retrieve pending competency validation records."""
        master_id = "master-pv-1"
        learner_id = "learner-pv-1"
        cohort_id = "cohort-pv-1"

        cohort = create_cohort(cohort_id=cohort_id, master_id=master_id)
        cohort.enrol_learner("m-pv-1", learner_id)

        pending = _make_pending_competency(
            pending_id="pcv-1",
            learner_id=learner_id,
            topic_id="topic-pv-1",
            cohort_id=cohort_id,
        )

        with api_client.app.dependency_overrides[get_cohort_uow]() as uow:
            uow.cohorts.save(cohort)
            uow.pending_competency_validations.save(pending)
            uow.commit()

        resp = api_client.get(
            f"/cohorts/{cohort_id}/pending-competency-validations",
            headers=_auth_headers(master_id),
        )

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["pending_id"] == "pcv-1"
        assert data[0]["learner_id"] == learner_id
        assert data[0]["topic_id"] == "topic-pv-1"
        assert data[0]["cohort_id"] == cohort_id

    def test_curator_gets_pending_validations(self, api_client: TestClient):
        """Module Curator can also retrieve pending competency validation records."""
        master_id = "master-pv-2"
        curator_id = "curator-pv-2"
        learner_id = "learner-pv-2"
        cohort_id = "cohort-pv-2"

        cohort = create_cohort(cohort_id=cohort_id, master_id=master_id)
        cohort.enrol_learner("m-pv-2a", curator_id)
        cohort.enrol_learner("m-pv-2b", learner_id)
        # Elevate curator_id to MODULE_CURATOR
        cohort.memberships[0].promote_to(CohortRole.MODULE_CURATOR)

        pending = _make_pending_competency(
            pending_id="pcv-2",
            learner_id=learner_id,
            topic_id="topic-pv-2",
            cohort_id=cohort_id,
        )

        with api_client.app.dependency_overrides[get_cohort_uow]() as uow:
            uow.cohorts.save(cohort)
            uow.pending_competency_validations.save(pending)
            uow.commit()

        resp = api_client.get(
            f"/cohorts/{cohort_id}/pending-competency-validations",
            headers=_auth_headers(curator_id),
        )

        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_regular_learner_gets_403(self, api_client: TestClient):
        """Regular learner cannot access pending competency validations."""
        master_id = "master-pv-3"
        learner_id = "learner-pv-3"
        cohort_id = "cohort-pv-3"

        cohort = create_cohort(cohort_id=cohort_id, master_id=master_id)
        cohort.enrol_learner("m-pv-3", learner_id)

        with api_client.app.dependency_overrides[get_cohort_uow]() as uow:
            uow.cohorts.save(cohort)
            uow.commit()

        resp = api_client.get(
            f"/cohorts/{cohort_id}/pending-competency-validations",
            headers=_auth_headers(learner_id),
        )

        assert resp.status_code == 403

    def test_stale_records_filtered_out(self, api_client: TestClient):
        """Pending records for already-validated learners are excluded from results."""
        master_id = "master-pv-4"
        learner_id = "learner-pv-4"
        cohort_id = "cohort-pv-4"
        topic_id = "topic-pv-4"

        cohort = create_cohort(cohort_id=cohort_id, master_id=master_id)
        cohort.enrol_learner("m-pv-4", learner_id)

        pending = _make_pending_competency(
            pending_id="pcv-4",
            learner_id=learner_id,
            topic_id=topic_id,
            cohort_id=cohort_id,
        )

        # Add a TopicCompetency record to mark the learner as already validated
        from cohort_learning.domain.topic_competency import TopicCompetency

        competency = TopicCompetency(
            competency_id="comp-pv-4",
            learner_id=learner_id,
            topic_id=topic_id,
            cohort_id=cohort_id,
        )

        with api_client.app.dependency_overrides[get_cohort_uow]() as uow:
            uow.cohorts.save(cohort)
            uow.pending_competency_validations.save(pending)
            uow._session.merge(competency)
            uow.commit()

        resp = api_client.get(
            f"/cohorts/{cohort_id}/pending-competency-validations",
            headers=_auth_headers(master_id),
        )

        assert resp.status_code == 200
        # Stale record filtered out
        assert resp.json() == []

    def test_unknown_cohort_returns_404(self, api_client: TestClient):
        """Returns 404 for a cohort that does not exist."""
        resp = api_client.get(
            "/cohorts/no-such-cohort/pending-competency-validations",
            headers=_auth_headers("some-user"),
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Tests: GET pending-curator-promotions
# ---------------------------------------------------------------------------


class TestGetPendingCuratorPromotions:
    def test_master_gets_pending_promotions(self, api_client: TestClient):
        """Master can retrieve pending curator promotion records."""
        master_id = "master-pp-1"
        learner_id = "learner-pp-1"
        cohort_id = "cohort-pp-1"

        cohort = create_cohort(cohort_id=cohort_id, master_id=master_id)
        cohort.enrol_learner("m-pp-1", learner_id)

        pending = _make_pending_curator(
            pending_id="pcp-1",
            learner_id=learner_id,
            module_id="module-pp-1",
            cohort_id=cohort_id,
        )

        with api_client.app.dependency_overrides[get_cohort_uow]() as uow:
            uow.cohorts.save(cohort)
            uow.pending_curator_promotions.save(pending)
            uow.commit()

        resp = api_client.get(
            f"/cohorts/{cohort_id}/pending-curator-promotions",
            headers=_auth_headers(master_id),
        )

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["pending_id"] == "pcp-1"
        assert data[0]["learner_id"] == learner_id
        assert data[0]["module_id"] == "module-pp-1"
        assert data[0]["cohort_id"] == cohort_id

    def test_curator_gets_403(self, api_client: TestClient):
        """Module Curator cannot access pending curator promotions (Master-only)."""
        master_id = "master-pp-2"
        curator_id = "curator-pp-2"
        cohort_id = "cohort-pp-2"

        cohort = create_cohort(cohort_id=cohort_id, master_id=master_id)
        cohort.enrol_learner("m-pp-2", curator_id)
        cohort.memberships[0].promote_to(CohortRole.MODULE_CURATOR)

        with api_client.app.dependency_overrides[get_cohort_uow]() as uow:
            uow.cohorts.save(cohort)
            uow.commit()

        resp = api_client.get(
            f"/cohorts/{cohort_id}/pending-curator-promotions",
            headers=_auth_headers(curator_id),
        )

        assert resp.status_code == 403

    def test_regular_learner_gets_403(self, api_client: TestClient):
        """Regular learner cannot access pending curator promotions."""
        master_id = "master-pp-3"
        learner_id = "learner-pp-3"
        cohort_id = "cohort-pp-3"

        cohort = create_cohort(cohort_id=cohort_id, master_id=master_id)
        cohort.enrol_learner("m-pp-3", learner_id)

        with api_client.app.dependency_overrides[get_cohort_uow]() as uow:
            uow.cohorts.save(cohort)
            uow.commit()

        resp = api_client.get(
            f"/cohorts/{cohort_id}/pending-curator-promotions",
            headers=_auth_headers(learner_id),
        )

        assert resp.status_code == 403

    def test_stale_records_filtered_out(self, api_client: TestClient):
        """Pending records for already-promoted learners are excluded."""
        master_id = "master-pp-4"
        learner_id = "learner-pp-4"
        cohort_id = "cohort-pp-4"
        module_id = "module-pp-4"

        cohort = create_cohort(cohort_id=cohort_id, master_id=master_id)
        cohort.enrol_learner("m-pp-4", learner_id)

        pending = _make_pending_curator(
            pending_id="pcp-4",
            learner_id=learner_id,
            module_id=module_id,
            cohort_id=cohort_id,
        )

        # Learner is already a ModuleCurator
        curator_record = create_module_curator(
            curator_id="cur-pp-4",
            learner_id=learner_id,
            module_id=module_id,
            cohort_id=cohort_id,
            promoted_by=master_id,
        )

        with api_client.app.dependency_overrides[get_cohort_uow]() as uow:
            uow.cohorts.save(cohort)
            uow.pending_curator_promotions.save(pending)
            uow.module_curators.save(curator_record)
            uow.commit()

        resp = api_client.get(
            f"/cohorts/{cohort_id}/pending-curator-promotions",
            headers=_auth_headers(master_id),
        )

        assert resp.status_code == 200
        assert resp.json() == []

    def test_unknown_cohort_returns_404(self, api_client: TestClient):
        """Returns 404 for a cohort that does not exist."""
        resp = api_client.get(
            "/cohorts/no-such-cohort/pending-curator-promotions",
            headers=_auth_headers("some-user"),
        )
        assert resp.status_code == 404
