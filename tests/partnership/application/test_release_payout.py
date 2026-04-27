"""Tests for ReleasePayoutUseCase (Stage 11 — RED phase)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from partnership.application.release_payout import ReleasePayoutUseCase
from partnership.domain.commission import Commission, CommissionStatus
from tests.partnership.fakes.fake_unit_of_work import FakeUnitOfWork

_NOW = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
_30_DAYS = timedelta(days=30)
_ELIGIBLE_AT = _NOW + _30_DAYS


def _seed_commission(
    uow: FakeUnitOfWork,
    *,
    commission_id: str = "com-1",
    curator_id: str = "curator-1",
    base_amount: Decimal = Decimal("100.00"),
    earned_at: datetime = _NOW,
) -> Commission:
    """Create and save a commission directly in the fake UoW (bypassing use case)."""
    commission = Commission.create(
        commission_id=commission_id,
        curator_id=curator_id,
        cohort_id="cohort-1",
        module_id="module-1",
        base_amount=base_amount,
        bonus_amount=Decimal("0.00"),
        earned_at=earned_at,
    )
    commission.collect_events()  # drain creation events
    uow.commissions._storage[commission_id] = commission
    return commission


class TestReleasePayoutUseCase:
    def _make_uc(self, uow: FakeUnitOfWork) -> ReleasePayoutUseCase:
        return ReleasePayoutUseCase(uow)

    def test_releases_eligible_commission_successfully(self) -> None:
        uow = FakeUnitOfWork()
        _seed_commission(uow, earned_at=_NOW)
        uc = self._make_uc(uow)
        release_time = _ELIGIBLE_AT + timedelta(seconds=1)

        result = uc.execute(
            commission_id="com-1",
            curator_id="curator-1",
            now=release_time,
        )

        assert result.status == CommissionStatus.RELEASED

    def test_raises_lookup_error_when_commission_not_found(self) -> None:
        uow = FakeUnitOfWork()
        uc = self._make_uc(uow)

        with pytest.raises(LookupError, match="com-999"):
            uc.execute(
                commission_id="com-999",
                curator_id="curator-1",
                now=_ELIGIBLE_AT + timedelta(seconds=1),
            )

    def test_raises_permission_error_when_curator_id_mismatch(self) -> None:
        uow = FakeUnitOfWork()
        _seed_commission(uow, curator_id="curator-1", earned_at=_NOW)
        uc = self._make_uc(uow)

        with pytest.raises(PermissionError, match="curator-2"):
            uc.execute(
                commission_id="com-1",
                curator_id="curator-2",
                now=_ELIGIBLE_AT + timedelta(seconds=1),
            )

    def test_propagates_value_error_if_hold_period_not_elapsed(self) -> None:
        uow = FakeUnitOfWork()
        _seed_commission(uow, earned_at=_NOW)
        uc = self._make_uc(uow)

        with pytest.raises(ValueError, match="hold period"):
            uc.execute(
                commission_id="com-1",
                curator_id="curator-1",
                now=_NOW,  # before hold period
            )

    def test_propagates_value_error_if_below_minimum_threshold(self) -> None:
        uow = FakeUnitOfWork()
        _seed_commission(uow, base_amount=Decimal("30.00"), earned_at=_NOW)
        uc = self._make_uc(uow)

        with pytest.raises(ValueError, match="minimum threshold"):
            uc.execute(
                commission_id="com-1",
                curator_id="curator-1",
                now=_ELIGIBLE_AT + timedelta(seconds=1),
            )

    def test_propagates_value_error_if_already_released(self) -> None:
        uow = FakeUnitOfWork()
        commission = _seed_commission(uow, earned_at=_NOW)
        release_time = _ELIGIBLE_AT + timedelta(seconds=1)
        commission.release(now=release_time)
        commission.collect_events()

        uc = self._make_uc(uow)

        with pytest.raises(ValueError, match="already released"):
            uc.execute(
                commission_id="com-1",
                curator_id="curator-1",
                now=release_time + timedelta(days=1),
            )

    def test_commits_uow_on_success(self) -> None:
        uow = FakeUnitOfWork()
        _seed_commission(uow, earned_at=_NOW)
        uc = self._make_uc(uow)

        uc.execute(
            commission_id="com-1",
            curator_id="curator-1",
            now=_ELIGIBLE_AT + timedelta(seconds=1),
        )

        assert uow.committed is True

    def test_released_at_matches_provided_now(self) -> None:
        uow = FakeUnitOfWork()
        _seed_commission(uow, earned_at=_NOW)
        uc = self._make_uc(uow)
        release_time = _ELIGIBLE_AT + timedelta(hours=3)

        result = uc.execute(
            commission_id="com-1",
            curator_id="curator-1",
            now=release_time,
        )

        assert result.released_at == release_time
