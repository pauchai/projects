"""Integration tests for SqlAlchemyCommissionRepository.

Verifies round-trip persistence: save → find_by_id, find_by_curator, find_by_cohort.
Uses savepoint rollback for full isolation per test.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

# Trigger ORM mapping registration before any tests run
import partnership.infrastructure.orm  # noqa: F401
from partnership.domain.commission import Commission, CommissionStatus
from partnership.infrastructure.sqlalchemy_commission_repository import (
    SqlAlchemyCommissionRepository,
)
from partnership.infrastructure.sqlalchemy_unit_of_work import SqlAlchemyUnitOfWork


def _make_commission(
    commission_id: str = "comm-1",
    curator_id: str = "curator-1",
    cohort_id: str = "cohort-1",
    module_id: str = "module-1",
    base_amount: Decimal = Decimal("20.00"),
    bonus_amount: Decimal = Decimal("1.00"),
) -> Commission:
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return Commission.create(
        commission_id=commission_id,
        curator_id=curator_id,
        cohort_id=cohort_id,
        module_id=module_id,
        base_amount=base_amount,
        bonus_amount=bonus_amount,
        earned_at=now,
    )


class TestSqlAlchemyCommissionRepository:
    def test_save_and_find_by_id_round_trip(self, integration_session: Session) -> None:
        """Save a Commission and retrieve it by ID."""
        repo = SqlAlchemyCommissionRepository(integration_session)
        commission = _make_commission()
        commission.collect_events()  # clear events

        repo.save(commission)

        found = repo.find_by_id("comm-1")
        assert found is not None
        assert found.commission_id == "comm-1"
        assert found.curator_id == "curator-1"
        assert found.cohort_id == "cohort-1"
        assert found.module_id == "module-1"
        assert found.base_amount == Decimal("20.00")
        assert found.bonus_amount == Decimal("1.00")
        assert found.status == CommissionStatus.PENDING
        assert found.released_at is None

    def test_find_by_id_returns_none_for_missing(
        self, integration_session: Session
    ) -> None:
        """Returns None when the commission does not exist."""
        repo = SqlAlchemyCommissionRepository(integration_session)
        assert repo.find_by_id("nonexistent-commission") is None

    def test_find_by_curator_returns_all_commissions(
        self, integration_session: Session
    ) -> None:
        """find_by_curator returns all commissions for the given curator."""
        repo = SqlAlchemyCommissionRepository(integration_session)

        c1 = _make_commission(
            commission_id="comm-c1", curator_id="curator-X", cohort_id="cohort-A"
        )
        c2 = _make_commission(
            commission_id="comm-c2", curator_id="curator-X", cohort_id="cohort-B"
        )
        c3 = _make_commission(
            commission_id="comm-c3", curator_id="curator-Y", cohort_id="cohort-A"
        )

        for c in [c1, c2, c3]:
            c.collect_events()
            repo.save(c)

        results = repo.find_by_curator("curator-X")
        ids = {c.commission_id for c in results}
        assert ids == {"comm-c1", "comm-c2"}

    def test_find_by_curator_returns_empty_for_unknown(
        self, integration_session: Session
    ) -> None:
        """Returns empty list when curator has no commissions."""
        repo = SqlAlchemyCommissionRepository(integration_session)
        assert repo.find_by_curator("unknown-curator") == []

    def test_find_by_cohort_returns_matching_commissions(
        self, integration_session: Session
    ) -> None:
        """find_by_cohort returns all commissions for the given cohort."""
        repo = SqlAlchemyCommissionRepository(integration_session)

        c1 = _make_commission(
            commission_id="comm-ch1", curator_id="curator-A", cohort_id="cohort-ZZ"
        )
        c2 = _make_commission(
            commission_id="comm-ch2", curator_id="curator-B", cohort_id="cohort-ZZ"
        )
        c3 = _make_commission(
            commission_id="comm-ch3", curator_id="curator-A", cohort_id="cohort-OTHER"
        )

        for c in [c1, c2, c3]:
            c.collect_events()
            repo.save(c)

        results = repo.find_by_cohort("cohort-ZZ")
        ids = {c.commission_id for c in results}
        assert ids == {"comm-ch1", "comm-ch2"}

    def test_save_updates_existing_commission_status(
        self, integration_session: Session
    ) -> None:
        """Saving a commission with updated status persists the change."""
        repo = SqlAlchemyCommissionRepository(integration_session)

        # Create and save
        commission = _make_commission(
            commission_id="comm-upd-1",
            base_amount=Decimal("30.00"),
            bonus_amount=Decimal("25.00"),
        )
        commission.collect_events()
        repo.save(commission)

        # Load and release
        loaded = repo.find_by_id("comm-upd-1")
        assert loaded is not None
        # Release: hold period = 30 days from earned_at; use a far-future date
        far_future = datetime(2100, 1, 1, tzinfo=timezone.utc)
        loaded.release(now=far_future)
        loaded.collect_events()
        repo.save(loaded)

        # Verify status persisted
        updated = repo.find_by_id("comm-upd-1")
        assert updated is not None
        assert updated.status == CommissionStatus.RELEASED
        assert updated.released_at == far_future

    def test_transient_events_initialised_after_load(
        self, integration_session: Session
    ) -> None:
        """Commission loaded from DB has _events list initialised (empty)."""
        repo = SqlAlchemyCommissionRepository(integration_session)
        commission = _make_commission(commission_id="comm-ev-1")
        commission.collect_events()
        repo.save(commission)

        loaded = repo.find_by_id("comm-ev-1")
        assert loaded is not None
        assert hasattr(loaded, "_events")
        assert loaded._events == []

    def test_uow_round_trip_with_session_factory(
        self, integration_session_factory: object
    ) -> None:
        """Full UoW round-trip: save via UoW, find after commit."""
        uow = SqlAlchemyUnitOfWork(integration_session_factory)  # type: ignore[arg-type]

        commission = _make_commission(commission_id="comm-uow-1")

        with uow:
            uow.commissions.save(commission)
            uow.commit()

        with uow:
            found = uow.commissions.find_by_id("comm-uow-1")
            assert found is not None
            assert found.commission_id == "comm-uow-1"
