"""API integration tests for Rewards endpoints.

Uses TestClient + test database with rolled-back transactions.

Tests verify:
- GET /me/rewards              — own balance (empty and with entries)
- GET /me/rewards/history      — full reward entry history
- GET /cohorts/{id}/leaderboard — XP leaderboard (sorted, 403, 404)
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
from cohort_learning.domain.reward_ledger import RewardLedger
from cohort_learning.infrastructure.sqlalchemy_unit_of_work import (
    SqlAlchemyUnitOfWork as CohortUnitOfWork,
)
from project_collaboration.api.app import create_app
from project_collaboration.infrastructure.database import (
    TEST_DATABASE_URL,
    get_engine,
)
from shared_kernel.migration import run_migrations
from tests.cohort_learning.factories import create_cohort


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------

TEST_JWT_SECRET = "test-rewards-secret"
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
# Tests: GET /me/rewards
# ---------------------------------------------------------------------------


class TestGetMyRewardBalance:
    def test_returns_empty_balance_when_no_ledger_exists(
        self, api_client: TestClient
    ) -> None:
        """Returns a zero-valued balance when the learner has never been rewarded."""
        learner_id = "learner-rew-empty"

        resp = api_client.get("/me/rewards", headers=_auth_headers(learner_id))

        assert resp.status_code == 200
        data = resp.json()
        assert data["learner_id"] == learner_id
        assert data["total_xp"] == 0
        assert data["total_credits"] == 0
        assert data["badges"] == []
        assert data["reputation_score"] is None

    def test_returns_correct_balance_with_multiple_reward_types(
        self, api_client: TestClient
    ) -> None:
        """Balance correctly aggregates XP, credits, badge, and reputation."""
        learner_id = "learner-rew-multi"
        now = datetime.now(UTC)

        ledger = RewardLedger(learner_id=learner_id)
        ledger.add_xp(
            entry_id="e-m1",
            amount=100,
            triggering_event="ExpertRewardGranted",
            granted_at=now,
            cohort_id="c1",
        )
        ledger.add_xp(
            entry_id="e-m2",
            amount=50,
            triggering_event="ExpertRewardGranted",
            granted_at=now,
            cohort_id="c1",
        )
        ledger.add_credits(
            entry_id="e-m3",
            amount=10,
            triggering_event=None,
            granted_at=now,
        )
        ledger.add_badge(
            entry_id="e-m4",
            topic_id="topic-python",
            triggering_event=None,
            granted_at=now,
        )
        ledger.update_reputation(entry_id="e-m5", score=42, granted_at=now)

        with api_client.app.dependency_overrides[get_cohort_uow]() as uow:
            uow.reward_ledgers.save(ledger)
            uow.commit()

        resp = api_client.get("/me/rewards", headers=_auth_headers(learner_id))

        assert resp.status_code == 200
        data = resp.json()
        assert data["learner_id"] == learner_id
        assert data["total_xp"] == 150
        assert data["total_credits"] == 10
        assert data["badges"] == ["topic-python"]
        assert data["reputation_score"] == 42

    def test_credits_are_capped_at_50_in_balance(self, api_client: TestClient) -> None:
        """Total credits shown cannot exceed 50 even when raw sum is higher."""
        learner_id = "learner-rew-cap"
        now = datetime.now(UTC)

        ledger = RewardLedger(learner_id=learner_id)
        ledger.add_credits(
            entry_id="e-cap1", amount=30, triggering_event=None, granted_at=now
        )
        ledger.add_credits(
            entry_id="e-cap2", amount=30, triggering_event=None, granted_at=now
        )

        with api_client.app.dependency_overrides[get_cohort_uow]() as uow:
            uow.reward_ledgers.save(ledger)
            uow.commit()

        resp = api_client.get("/me/rewards", headers=_auth_headers(learner_id))

        assert resp.status_code == 200
        assert resp.json()["total_credits"] == 50

    def test_returns_401_without_authentication(self, api_client: TestClient) -> None:
        """Unauthenticated requests are rejected with 401."""
        resp = api_client.get("/me/rewards")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Tests: GET /me/rewards/history
# ---------------------------------------------------------------------------


class TestGetMyRewardHistory:
    def test_returns_empty_list_when_no_ledger_exists(
        self, api_client: TestClient
    ) -> None:
        """Returns an empty list when the learner has no reward history."""
        learner_id = "learner-hist-empty"

        resp = api_client.get("/me/rewards/history", headers=_auth_headers(learner_id))

        assert resp.status_code == 200
        assert resp.json() == []

    def test_returns_all_entries_in_insertion_order(
        self, api_client: TestClient
    ) -> None:
        """History contains every entry in the order they were granted."""
        learner_id = "learner-hist-full"
        now = datetime.now(UTC)

        ledger = RewardLedger(learner_id=learner_id)
        ledger.add_xp(
            entry_id="h1",
            amount=20,
            triggering_event=None,
            granted_at=now,
            cohort_id="c-h1",
        )
        ledger.add_badge(
            entry_id="h2",
            topic_id="topic-1",
            triggering_event=None,
            granted_at=now,
        )
        ledger.add_credits(
            entry_id="h3",
            amount=5,
            triggering_event=None,
            granted_at=now,
        )
        ledger.update_reputation(entry_id="h4", score=10, granted_at=now)

        with api_client.app.dependency_overrides[get_cohort_uow]() as uow:
            uow.reward_ledgers.save(ledger)
            uow.commit()

        resp = api_client.get("/me/rewards/history", headers=_auth_headers(learner_id))

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 4

        assert data[0]["entry_id"] == "h1"
        assert data[0]["reward_type"] == "xp"
        assert data[0]["amount"] == 20
        assert data[0]["cohort_id"] == "c-h1"
        assert data[0]["learner_id"] == learner_id

        assert data[1]["entry_id"] == "h2"
        assert data[1]["reward_type"] == "badge"
        assert data[1]["amount"] is None
        assert data[1]["metadata"] == {"badge_topic_id": "topic-1"}

        assert data[2]["entry_id"] == "h3"
        assert data[2]["reward_type"] == "credits"
        assert data[2]["amount"] == 5

        assert data[3]["entry_id"] == "h4"
        assert data[3]["reward_type"] == "reputation"
        assert data[3]["amount"] == 10

    def test_returns_401_without_authentication(self, api_client: TestClient) -> None:
        """Unauthenticated requests are rejected with 401."""
        resp = api_client.get("/me/rewards/history")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Tests: GET /cohorts/{cohort_id}/leaderboard
# ---------------------------------------------------------------------------


class TestGetCohortXpLeaderboard:
    def test_returns_members_ranked_by_xp_descending(
        self, api_client: TestClient
    ) -> None:
        """Leaderboard lists all cohort members ranked highest XP first."""
        master_id = "master-lb-1"
        learner1 = "learner-lb-1"
        learner2 = "learner-lb-2"
        cohort = create_cohort(cohort_id="cohort-lb-1", master_id=master_id)
        cohort.enrol_learner("m-lb-1", learner1)
        cohort.enrol_learner("m-lb-2", learner2)

        now = datetime.now(UTC)
        ledger1 = RewardLedger(learner_id=learner1)
        ledger1.add_xp(
            entry_id="lb-e1", amount=200, triggering_event=None, granted_at=now
        )
        ledger2 = RewardLedger(learner_id=learner2)
        ledger2.add_xp(
            entry_id="lb-e2", amount=50, triggering_event=None, granted_at=now
        )

        with api_client.app.dependency_overrides[get_cohort_uow]() as uow:
            uow.cohorts.save(cohort)
            uow.reward_ledgers.save(ledger1)
            uow.reward_ledgers.save(ledger2)
            uow.commit()

        resp = api_client.get(
            "/cohorts/cohort-lb-1/leaderboard",
            headers=_auth_headers(master_id),
        )

        assert resp.status_code == 200
        data = resp.json()
        # master + 2 learners = 3 entries
        assert len(data) == 3

        assert data[0]["learner_id"] == learner1
        assert data[0]["total_xp"] == 200
        assert data[0]["rank"] == 1

        assert data[1]["learner_id"] == learner2
        assert data[1]["total_xp"] == 50
        assert data[1]["rank"] == 2

        # Master has no ledger → 0 XP, last place
        assert data[2]["learner_id"] == master_id
        assert data[2]["total_xp"] == 0
        assert data[2]["rank"] == 3

    def test_member_can_view_leaderboard(self, api_client: TestClient) -> None:
        """A regular cohort member (not only master) can view the leaderboard."""
        master_id = "master-lb-2"
        learner_id = "learner-lb-3"
        cohort = create_cohort(cohort_id="cohort-lb-2", master_id=master_id)
        cohort.enrol_learner("m-lb-3", learner_id)

        with api_client.app.dependency_overrides[get_cohort_uow]() as uow:
            uow.cohorts.save(cohort)
            uow.commit()

        resp = api_client.get(
            "/cohorts/cohort-lb-2/leaderboard",
            headers=_auth_headers(learner_id),
        )

        assert resp.status_code == 200
        data = resp.json()
        # master + 1 learner
        assert len(data) == 2
        learner_ids = {e["learner_id"] for e in data}
        assert master_id in learner_ids
        assert learner_id in learner_ids

    def test_learners_without_ledger_appear_with_zero_xp(
        self, api_client: TestClient
    ) -> None:
        """Members who have never received rewards appear at the bottom with 0 XP."""
        master_id = "master-lb-4"
        learner_id = "learner-lb-4"
        cohort = create_cohort(cohort_id="cohort-lb-4", master_id=master_id)
        cohort.enrol_learner("m-lb-4", learner_id)

        with api_client.app.dependency_overrides[get_cohort_uow]() as uow:
            uow.cohorts.save(cohort)
            uow.commit()

        resp = api_client.get(
            "/cohorts/cohort-lb-4/leaderboard",
            headers=_auth_headers(master_id),
        )

        assert resp.status_code == 200
        data = resp.json()
        assert all(e["total_xp"] == 0 for e in data)
        ranks = [e["rank"] for e in data]
        assert sorted(ranks) == ranks  # ranks are in ascending order

    def test_returns_404_for_nonexistent_cohort(self, api_client: TestClient) -> None:
        """Returns 404 when the cohort does not exist."""
        resp = api_client.get(
            "/cohorts/nonexistent-cohort-lb/leaderboard",
            headers=_auth_headers("some-user"),
        )
        assert resp.status_code == 404

    def test_returns_403_when_caller_is_not_cohort_member(
        self, api_client: TestClient
    ) -> None:
        """An outsider who is not a member of the cohort cannot view the leaderboard."""
        master_id = "master-lb-5"
        outsider = "outsider-lb-1"
        cohort = create_cohort(cohort_id="cohort-lb-5", master_id=master_id)

        with api_client.app.dependency_overrides[get_cohort_uow]() as uow:
            uow.cohorts.save(cohort)
            uow.commit()

        resp = api_client.get(
            "/cohorts/cohort-lb-5/leaderboard",
            headers=_auth_headers(outsider),
        )
        assert resp.status_code == 403

    def test_returns_401_without_authentication(self, api_client: TestClient) -> None:
        """Unauthenticated requests are rejected with 401."""
        resp = api_client.get("/cohorts/any-cohort/leaderboard")
        assert resp.status_code == 401
