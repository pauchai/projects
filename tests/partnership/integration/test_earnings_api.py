"""API integration tests for Partnership Earnings endpoints.

Uses TestClient + test database with rolled-back transactions.

Tests verify:
- GET /me/earnings           — earnings summary (empty and with commissions)
- GET /me/earnings/history   — full commission history
- POST /me/earnings/{id}/release — release payout (happy path + error cases)
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Connection, Engine, event
from sqlalchemy.orm import Session

# Trigger ORM mapping registration
import partnership.infrastructure.orm  # noqa: F401
from auth.api.dependencies import get_auth_uow, get_password_hasher, get_token_service
from auth.infrastructure.jwt_token_service import JwtTokenService
from partnership.api.dependencies import get_partnership_uow
from partnership.domain.commission import Commission, CommissionStatus
from partnership.infrastructure.sqlalchemy_unit_of_work import (
    SqlAlchemyUnitOfWork as PartnershipUnitOfWork,
)
from project_collaboration.api.app import create_app
from project_collaboration.infrastructure.database import (
    TEST_DATABASE_URL,
    get_engine,
)
from shared_kernel.migration import run_migrations


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------

TEST_JWT_SECRET = "test-partnership-secret"
_test_token_service = JwtTokenService(
    secret=TEST_JWT_SECRET, algorithm="HS256", expire_minutes=60
)


def _auth_headers(user_id: str) -> dict[str, str]:
    """Create Authorization headers with a valid JWT for the given user_id."""
    token = _test_token_service.create_access_token(user_id)
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Test data helpers
# ---------------------------------------------------------------------------


def _make_commission(
    commission_id: str,
    curator_id: str,
    cohort_id: str = "cohort-1",
    module_id: str = "module-1",
    base_amount: Decimal = Decimal("30.00"),
    bonus_amount: Decimal = Decimal("25.00"),
    days_offset: int = -40,  # default: earned 40 days ago (past hold period)
) -> Commission:
    earned_at = datetime.now(timezone.utc) + timedelta(days=days_offset)
    return Commission.create(
        commission_id=commission_id,
        curator_id=curator_id,
        cohort_id=cohort_id,
        module_id=module_id,
        base_amount=base_amount,
        bonus_amount=bonus_amount,
        earned_at=earned_at,
    )


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
    """Create a TestClient whose Partnership UoW is bound to a rolled-back transaction."""
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

    def _partnership_uow_override():
        uow = PartnershipUnitOfWork(factory)  # type: ignore[arg-type]
        uow._session = session
        return uow

    app.dependency_overrides[get_partnership_uow] = _partnership_uow_override
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
# Tests: GET /me/earnings
# ---------------------------------------------------------------------------


class TestGetMyEarningsSummary:
    def test_returns_empty_summary_when_no_commissions(
        self, api_client: TestClient
    ) -> None:
        """Returns zero totals and empty list when curator has no commissions."""
        curator_id = "curator-earn-empty"

        resp = api_client.get("/me/earnings", headers=_auth_headers(curator_id))

        assert resp.status_code == 200
        data = resp.json()
        assert data["curator_id"] == curator_id
        assert Decimal(data["total_pending"]) == Decimal("0")
        assert Decimal(data["total_released"]) == Decimal("0")
        assert data["commissions"] == []

    def test_returns_pending_total_correctly(self, api_client: TestClient) -> None:
        """total_pending sums base + bonus for PENDING commissions."""
        curator_id = "curator-earn-pending"
        commission = _make_commission(
            commission_id="c-earn-1",
            curator_id=curator_id,
            base_amount=Decimal("30.00"),
            bonus_amount=Decimal("5.00"),
        )
        commission.collect_events()

        with api_client.app.dependency_overrides[get_partnership_uow]() as uow:
            uow.commissions.save(commission)
            uow.commit()

        resp = api_client.get("/me/earnings", headers=_auth_headers(curator_id))

        assert resp.status_code == 200
        data = resp.json()
        assert Decimal(data["total_pending"]) == Decimal("35.00")
        assert Decimal(data["total_released"]) == Decimal("0")
        assert len(data["commissions"]) == 1

    def test_commission_response_fields(self, api_client: TestClient) -> None:
        """CommissionResponse contains all expected fields."""
        curator_id = "curator-earn-fields"
        commission = _make_commission(
            commission_id="c-fields-1",
            curator_id=curator_id,
            cohort_id="cohort-fields",
            module_id="module-fields",
            base_amount=Decimal("20.00"),
            bonus_amount=Decimal("1.00"),
        )
        commission.collect_events()

        with api_client.app.dependency_overrides[get_partnership_uow]() as uow:
            uow.commissions.save(commission)
            uow.commit()

        resp = api_client.get("/me/earnings", headers=_auth_headers(curator_id))

        assert resp.status_code == 200
        c = resp.json()["commissions"][0]
        assert c["commission_id"] == "c-fields-1"
        assert c["curator_id"] == curator_id
        assert c["cohort_id"] == "cohort-fields"
        assert c["module_id"] == "module-fields"
        assert Decimal(c["base_amount"]) == Decimal("20.00")
        assert Decimal(c["bonus_amount"]) == Decimal("1.00")
        assert Decimal(c["total_amount"]) == Decimal("21.00")
        assert c["status"] == CommissionStatus.PENDING.value
        assert c["released_at"] is None

    def test_returns_401_without_authentication(self, api_client: TestClient) -> None:
        resp = api_client.get("/me/earnings")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Tests: GET /me/earnings/history
# ---------------------------------------------------------------------------


class TestGetMyEarningsHistory:
    def test_returns_empty_list_when_no_commissions(
        self, api_client: TestClient
    ) -> None:
        curator_id = "curator-hist-empty"
        resp = api_client.get("/me/earnings/history", headers=_auth_headers(curator_id))
        assert resp.status_code == 200
        assert resp.json() == []

    def test_returns_all_commissions(self, api_client: TestClient) -> None:
        """History returns all commissions for the curator."""
        curator_id = "curator-hist-full"

        c1 = _make_commission(commission_id="c-hist-1", curator_id=curator_id)
        c2 = _make_commission(
            commission_id="c-hist-2", curator_id=curator_id, cohort_id="cohort-2"
        )

        for c in [c1, c2]:
            c.collect_events()

        with api_client.app.dependency_overrides[get_partnership_uow]() as uow:
            uow.commissions.save(c1)
            uow.commissions.save(c2)
            uow.commit()

        resp = api_client.get("/me/earnings/history", headers=_auth_headers(curator_id))

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        ids = {c["commission_id"] for c in data}
        assert ids == {"c-hist-1", "c-hist-2"}

    def test_returns_401_without_authentication(self, api_client: TestClient) -> None:
        resp = api_client.get("/me/earnings/history")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Tests: POST /me/earnings/{commission_id}/release
# ---------------------------------------------------------------------------


class TestReleaseEarning:
    def test_releases_eligible_commission_successfully(
        self, api_client: TestClient
    ) -> None:
        """Successfully releases a PENDING commission past the hold period."""
        curator_id = "curator-rel-ok"
        commission = _make_commission(
            commission_id="c-rel-ok",
            curator_id=curator_id,
            base_amount=Decimal("30.00"),
            bonus_amount=Decimal("25.00"),
            days_offset=-40,  # 40 days ago, past hold period
        )
        commission.collect_events()

        with api_client.app.dependency_overrides[get_partnership_uow]() as uow:
            uow.commissions.save(commission)
            uow.commit()

        resp = api_client.post(
            "/me/earnings/c-rel-ok/release",
            headers=_auth_headers(curator_id),
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["commission_id"] == "c-rel-ok"
        assert data["status"] == CommissionStatus.RELEASED.value
        assert data["released_at"] is not None

    def test_returns_404_for_nonexistent_commission(
        self, api_client: TestClient
    ) -> None:
        curator_id = "curator-rel-404"
        resp = api_client.post(
            "/me/earnings/nonexistent-commission/release",
            headers=_auth_headers(curator_id),
        )
        assert resp.status_code == 404

    def test_returns_403_when_not_commission_owner(
        self, api_client: TestClient
    ) -> None:
        """A curator cannot release another curator's commission."""
        owner_id = "curator-rel-owner"
        intruder_id = "curator-rel-intruder"

        commission = _make_commission(
            commission_id="c-rel-403",
            curator_id=owner_id,
            base_amount=Decimal("30.00"),
            bonus_amount=Decimal("25.00"),
        )
        commission.collect_events()

        with api_client.app.dependency_overrides[get_partnership_uow]() as uow:
            uow.commissions.save(commission)
            uow.commit()

        resp = api_client.post(
            "/me/earnings/c-rel-403/release",
            headers=_auth_headers(intruder_id),
        )
        assert resp.status_code == 403

    def test_returns_422_when_hold_period_not_elapsed(
        self, api_client: TestClient
    ) -> None:
        """Returns 422 when the hold period has not elapsed yet."""
        curator_id = "curator-rel-hold"
        commission = _make_commission(
            commission_id="c-rel-hold",
            curator_id=curator_id,
            base_amount=Decimal("30.00"),
            bonus_amount=Decimal("25.00"),
            days_offset=0,  # earned today — hold period not elapsed
        )
        commission.collect_events()

        with api_client.app.dependency_overrides[get_partnership_uow]() as uow:
            uow.commissions.save(commission)
            uow.commit()

        resp = api_client.post(
            "/me/earnings/c-rel-hold/release",
            headers=_auth_headers(curator_id),
        )
        assert resp.status_code == 422

    def test_returns_401_without_authentication(self, api_client: TestClient) -> None:
        resp = api_client.post("/me/earnings/some-commission/release")
        assert resp.status_code == 401
