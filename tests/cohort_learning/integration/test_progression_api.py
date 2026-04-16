"""API integration tests for Partner Progression endpoints.

Uses TestClient + test database with rolled-back transactions.

Tests verify:
- POST /cohorts/{cohort_id}/members/{learner_id}/validate-competency
- POST /cohorts/{cohort_id}/members/{learner_id}/promote-expert
- POST /cohorts/{cohort_id}/members/{learner_id}/promote-curator
- GET /cohorts/{cohort_id}/helper-metrics
- GET /cohorts/{cohort_id}/topic-experts
- Authorization rules (master/curator for validation/promotion, members for reads)
"""

from __future__ import annotations

from datetime import datetime, UTC
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Connection, Engine, event
from sqlalchemy.orm import Session

from auth.api.dependencies import get_auth_uow, get_password_hasher, get_token_service
from auth.infrastructure.jwt_token_service import JwtTokenService
from cohort_learning.api.dependencies import get_cohort_uow
from cohort_learning.domain.cohort_role import CohortRole
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
    create_helper_metrics,
    create_module_curator,
    create_topic_expert,
)


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------

TEST_JWT_SECRET = "test-progression-secret"
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
    """Create a TestClient whose UoW is bound to a rolled-back transaction."""
    connection = api_engine.connect()
    transaction = connection.begin()

    session = Session(bind=connection)
    session.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(sess: Session, txn: object) -> None:
        if not sess.in_nested_transaction():
            sess.begin_nested()

    # Store original methods before overriding
    original_close = session.close
    original_rollback = session.rollback

    # Prevent UoW.__exit__ from destroying the shared session
    session.close = lambda: None  # type: ignore[assignment]
    session.rollback = lambda: None  # type: ignore[assignment]

    class _TestSessionFactory:
        """Always returns the same shared session."""

        def __call__(self) -> Session:
            return session

    factory = _TestSessionFactory()

    app = create_app()

    # Override cohort learning UoW
    def _cohort_uow_override():
        uow = CohortUnitOfWork(factory)  # type: ignore[arg-type]
        uow._session = session
        return uow

    app.dependency_overrides[get_cohort_uow] = _cohort_uow_override

    # Override token service to use test JWT secret
    app.dependency_overrides[get_token_service] = lambda: _test_token_service

    # Override auth-specific dependencies with no-ops
    def _noop_auth_uow():
        yield None

    app.dependency_overrides[get_auth_uow] = _noop_auth_uow
    app.dependency_overrides[get_password_hasher] = lambda: None

    client = TestClient(app)
    yield client

    # Rollback and cleanup
    transaction.rollback()
    session.close = original_close  # type: ignore[method-assign]
    session.rollback = original_rollback  # type: ignore[method-assign]
    session.close()
    connection.close()


# ---------------------------------------------------------------------------
# Tests: Validate Topic Competency
# ---------------------------------------------------------------------------


class TestValidateTopicCompetency:
    def test_validation_check_returns_missing_steps(self, api_client: TestClient):
        """Validation endpoint returns which steps are missing."""
        # Arrange: cohort with master and learner
        master_id = "master-1"
        learner_id = "learner-1"
        cohort = create_cohort(
            cohort_id="cohort-val-1",
            master_id=master_id,
            module_id="module-1",
        )
        cohort.enrol_learner("m-1", learner_id)

        with api_client.app.dependency_overrides[get_cohort_uow]() as uow:
            uow.cohorts.save(cohort)
            uow.commit()

        # Act: validate competency without any completed steps
        resp = api_client.post(
            f"/cohorts/cohort-val-1/members/{learner_id}/validate-competency",
            json={
                "topic_id": "topic-1",
                "knowledge_check_score": 0,
                "mentor_approved": False,
            },
            headers=_auth_headers(master_id),
        )

        # Assert
        assert resp.status_code == 200
        data = resp.json()
        assert data["topic_id"] == "topic-1"
        assert data["is_validated"] is False
        assert len(data["missing_steps"]) == 4  # all steps missing

    def test_validation_by_non_master_returns_403(self, api_client: TestClient):
        """Only master or curator can validate competency."""
        # Arrange
        master_id = "master-2"
        learner_id = "learner-2"
        other_learner = "learner-other"
        cohort = create_cohort(cohort_id="cohort-val-2", master_id=master_id)
        cohort.enrol_learner("m-1", learner_id)
        cohort.enrol_learner("m-2", other_learner)

        with api_client.app.dependency_overrides[get_cohort_uow]() as uow:
            uow.cohorts.save(cohort)
            uow.commit()

        # Act: validate as regular learner
        resp = api_client.post(
            f"/cohorts/cohort-val-2/members/{learner_id}/validate-competency",
            json={
                "topic_id": "topic-1",
                "knowledge_check_score": 80,
                "mentor_approved": True,
            },
            headers=_auth_headers(other_learner),
        )

        # Assert
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Tests: Promote to Topic Expert
# ---------------------------------------------------------------------------


class TestPromoteToTopicExpert:
    def test_promote_learner_to_expert_when_competent(self, api_client: TestClient):
        """Can promote learner to expert after competency validation."""
        # Arrange: cohort with learner who achieved competency
        master_id = "master-3"
        learner_id = "learner-3"
        cohort = create_cohort(cohort_id="cohort-exp-1", master_id=master_id)
        cohort.enrol_learner("m-1", learner_id)

        with api_client.app.dependency_overrides[get_cohort_uow]() as uow:
            uow.cohorts.save(cohort)
            # Mark competency as achieved (simplified for test)
            from cohort_learning.domain.topic_competency import TopicCompetency

            comp = TopicCompetency(
                competency_id="comp-1",
                learner_id=learner_id,
                topic_id="topic-1",
                cohort_id="cohort-exp-1",
            )
            uow._session.merge(comp)
            uow.commit()

        # Act: promote to expert
        resp = api_client.post(
            f"/cohorts/cohort-exp-1/members/{learner_id}/promote-expert",
            json={"expert_id": "exp-1", "topic_id": "topic-1"},
            headers=_auth_headers(master_id),
        )

        # Assert
        assert resp.status_code == 201
        data = resp.json()
        assert data["expert_id"] == "exp-1"
        assert data["learner_id"] == learner_id
        assert data["topic_id"] == "topic-1"
        assert data["validator_id"] == master_id

    def test_promote_without_competency_returns_400(self, api_client: TestClient):
        """Cannot promote without achieving competency."""
        # Arrange
        master_id = "master-4"
        learner_id = "learner-4"
        cohort = create_cohort(cohort_id="cohort-exp-2", master_id=master_id)
        cohort.enrol_learner("m-1", learner_id)

        with api_client.app.dependency_overrides[get_cohort_uow]() as uow:
            uow.cohorts.save(cohort)
            uow.commit()

        # Act: try to promote without competency
        resp = api_client.post(
            f"/cohorts/cohort-exp-2/members/{learner_id}/promote-expert",
            json={"expert_id": "exp-2", "topic_id": "topic-1"},
            headers=_auth_headers(master_id),
        )

        # Assert
        assert resp.status_code == 400
        assert "not achieved topic competency" in resp.json()["detail"].lower()

    def test_promote_by_non_master_returns_403(self, api_client: TestClient):
        """Only master or curator can promote to expert."""
        # Arrange
        master_id = "master-5"
        learner_id = "learner-5"
        other_learner = "learner-other-5"
        cohort = create_cohort(cohort_id="cohort-exp-3", master_id=master_id)
        cohort.enrol_learner("m-1", learner_id)
        cohort.enrol_learner("m-2", other_learner)

        with api_client.app.dependency_overrides[get_cohort_uow]() as uow:
            uow.cohorts.save(cohort)
            uow.commit()

        # Act: try to promote as regular learner
        resp = api_client.post(
            f"/cohorts/cohort-exp-3/members/{learner_id}/promote-expert",
            json={"expert_id": "exp-3", "topic_id": "topic-1"},
            headers=_auth_headers(other_learner),
        )

        # Assert
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Tests: Promote to Module Curator
# ---------------------------------------------------------------------------


class TestPromoteToModuleCurator:
    def test_promote_expert_to_curator_when_qualified(self, api_client: TestClient):
        """Can promote expert to curator when all requirements are met."""
        # Arrange: cohort with expert who meets helper thresholds
        master_id = "master-6"
        learner_id = "learner-6"
        cohort = create_cohort(
            cohort_id="cohort-cur-1",
            master_id=master_id,
            module_id="module-1",
        )
        cohort.enrol_learner("m-1", learner_id)

        with api_client.app.dependency_overrides[get_cohort_uow]() as uow:
            uow.cohorts.save(cohort)

            # Add topic expert record
            expert = create_topic_expert(
                expert_id="exp-cur-1",
                learner_id=learner_id,
                topic_id="topic-1",
                cohort_id="cohort-cur-1",
                validator_id=master_id,
            )
            uow.topic_experts.save(expert)

            # Add helper metrics that meet thresholds
            metrics = create_helper_metrics(
                learner_id=learner_id,
                cohort_id="cohort-cur-1",
                learners_helped=5,
                questions_answered=10,
                tasks_reviewed=8,
                average_satisfaction=Decimal("4.5"),
            )
            uow.helper_metrics.save(metrics)

            # Add module progression with topic
            from cohort_learning.domain.module_progression import ModuleProgression
            from cohort_learning.domain.topic import Topic

            module = ModuleProgression(
                module_id="module-1", title="Test Module", master_id=master_id
            )
            topic = Topic(
                topic_id="topic-1",
                title="Topic 1",
                position=1,
                description="Test topic",
            )
            module.add_topic(topic)
            uow._session.merge(module)

            uow.commit()

        # Act: promote to curator
        resp = api_client.post(
            f"/cohorts/cohort-cur-1/members/{learner_id}/promote-curator",
            json={"curator_id": "cur-1", "module_id": "module-1"},
            headers=_auth_headers(master_id),
        )

        # Assert
        assert resp.status_code == 201
        data = resp.json()
        assert data["curator_id"] == "cur-1"
        assert data["learner_id"] == learner_id
        assert data["module_id"] == "module-1"
        assert data["promoted_by"] == master_id

    def test_promote_without_helper_metrics_returns_400(self, api_client: TestClient):
        """Cannot promote without meeting helper thresholds."""
        # Arrange
        master_id = "master-7"
        learner_id = "learner-7"
        cohort = create_cohort(
            cohort_id="cohort-cur-2", master_id=master_id, module_id="module-2"
        )
        cohort.enrol_learner("m-1", learner_id)

        with api_client.app.dependency_overrides[get_cohort_uow]() as uow:
            uow.cohorts.save(cohort)

            # Expert but NO helper metrics
            expert = create_topic_expert(
                expert_id="exp-cur-2",
                learner_id=learner_id,
                topic_id="topic-1",
                cohort_id="cohort-cur-2",
                validator_id=master_id,
            )
            uow.topic_experts.save(expert)

            from cohort_learning.domain.module_progression import ModuleProgression
            from cohort_learning.domain.topic import Topic

            module = ModuleProgression(
                module_id="module-2", title="Module 2", master_id=master_id
            )
            topic = Topic(
                topic_id="topic-1", title="Topic 1", position=1, description="Test"
            )
            module.add_topic(topic)
            uow._session.merge(module)

            uow.commit()

        # Act
        resp = api_client.post(
            f"/cohorts/cohort-cur-2/members/{learner_id}/promote-curator",
            json={"curator_id": "cur-2", "module_id": "module-2"},
            headers=_auth_headers(master_id),
        )

        # Assert
        assert resp.status_code == 400
        assert "helper metrics" in resp.json()["detail"].lower()

    def test_promote_by_non_master_returns_403(self, api_client: TestClient):
        """Only master can promote to curator."""
        # Arrange
        master_id = "master-8"
        learner_id = "learner-8"
        curator_id = "curator-8"
        cohort = create_cohort(cohort_id="cohort-cur-3", master_id=master_id)
        cohort.enrol_learner("m-1", learner_id)
        cohort.enrol_learner("m-2", curator_id)
        # Promote curator_id to module curator role
        cohort.memberships[1]._role = CohortRole.MODULE_CURATOR

        with api_client.app.dependency_overrides[get_cohort_uow]() as uow:
            uow.cohorts.save(cohort)
            uow.commit()

        # Act: curator tries to promote another learner
        resp = api_client.post(
            f"/cohorts/cohort-cur-3/members/{learner_id}/promote-curator",
            json={"curator_id": "cur-3", "module_id": "module-1"},
            headers=_auth_headers(curator_id),
        )

        # Assert
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Tests: Get Helper Metrics
# ---------------------------------------------------------------------------


class TestGetHelperMetrics:
    def test_get_helper_metrics_for_cohort(self, api_client: TestClient):
        """Can retrieve helper metrics for all cohort members."""
        # Arrange
        master_id = "master-9"
        learner1 = "learner-9-1"
        learner2 = "learner-9-2"
        cohort = create_cohort(cohort_id="cohort-metrics-1", master_id=master_id)
        cohort.enrol_learner("m-1", learner1)
        cohort.enrol_learner("m-2", learner2)

        with api_client.app.dependency_overrides[get_cohort_uow]() as uow:
            uow.cohorts.save(cohort)

            # Add metrics for both learners
            metrics1 = create_helper_metrics(
                learner_id=learner1,
                cohort_id="cohort-metrics-1",
                learners_helped=3,
                tasks_reviewed=5,
                average_satisfaction=Decimal("4.2"),
            )
            metrics2 = create_helper_metrics(
                learner_id=learner2,
                cohort_id="cohort-metrics-1",
                learners_helped=1,
                tasks_reviewed=2,
                average_satisfaction=None,
            )
            uow.helper_metrics.save(metrics1)
            uow.helper_metrics.save(metrics2)
            uow.commit()

        # Act
        resp = api_client.get(
            "/cohorts/cohort-metrics-1/helper-metrics",
            headers=_auth_headers(master_id),
        )

        # Assert
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert any(m["learner_id"] == learner1 for m in data)
        assert any(m["learner_id"] == learner2 for m in data)

    def test_get_metrics_by_non_member_returns_403(self, api_client: TestClient):
        """Only cohort members can view helper metrics."""
        # Arrange
        master_id = "master-10"
        outsider = "outsider-10"
        cohort = create_cohort(cohort_id="cohort-metrics-2", master_id=master_id)

        with api_client.app.dependency_overrides[get_cohort_uow]() as uow:
            uow.cohorts.save(cohort)
            uow.commit()

        # Act: outsider tries to view metrics
        resp = api_client.get(
            "/cohorts/cohort-metrics-2/helper-metrics",
            headers=_auth_headers(outsider),
        )

        # Assert
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Tests: Get Topic Experts
# ---------------------------------------------------------------------------


class TestGetTopicExperts:
    def test_get_topic_experts_for_cohort(self, api_client: TestClient):
        """Can retrieve all topic experts in a cohort."""
        # Arrange
        master_id = "master-11"
        learner1 = "learner-11-1"
        learner2 = "learner-11-2"
        cohort = create_cohort(cohort_id="cohort-experts-1", master_id=master_id)
        cohort.enrol_learner("m-1", learner1)
        cohort.enrol_learner("m-2", learner2)

        with api_client.app.dependency_overrides[get_cohort_uow]() as uow:
            uow.cohorts.save(cohort)

            # Add topic experts
            expert1 = create_topic_expert(
                expert_id="exp-11-1",
                learner_id=learner1,
                topic_id="topic-1",
                cohort_id="cohort-experts-1",
                validator_id=master_id,
            )
            expert2 = create_topic_expert(
                expert_id="exp-11-2",
                learner_id=learner2,
                topic_id="topic-2",
                cohort_id="cohort-experts-1",
                validator_id=master_id,
            )
            uow.topic_experts.save(expert1)
            uow.topic_experts.save(expert2)
            uow.commit()

        # Act
        resp = api_client.get(
            "/cohorts/cohort-experts-1/topic-experts",
            headers=_auth_headers(master_id),
        )

        # Assert
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert any(e["expert_id"] == "exp-11-1" for e in data)
        assert any(e["expert_id"] == "exp-11-2" for e in data)

    def test_get_experts_by_non_member_returns_403(self, api_client: TestClient):
        """Only cohort members can view topic experts."""
        # Arrange
        master_id = "master-12"
        outsider = "outsider-12"
        cohort = create_cohort(cohort_id="cohort-experts-2", master_id=master_id)

        with api_client.app.dependency_overrides[get_cohort_uow]() as uow:
            uow.cohorts.save(cohort)
            uow.commit()

        # Act
        resp = api_client.get(
            "/cohorts/cohort-experts-2/topic-experts",
            headers=_auth_headers(outsider),
        )

        # Assert
        assert resp.status_code == 403
