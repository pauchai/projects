"""Unit tests for Commission aggregate (Stage 10 — RED phase)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from partnership.domain.commission import Commission, CommissionStatus
from partnership.domain.events import CurationCommissionEarned, PayoutReleased
from partnership.domain.value_objects import HoldPolicy, Payout

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_NOW = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
_30_DAYS = timedelta(days=30)
_ELIGIBLE_AT = _NOW + _30_DAYS


def _make_commission(
    *,
    base_amount: Decimal = Decimal("100.00"),
    bonus_amount: Decimal = Decimal("0.00"),
    earned_at: datetime = _NOW,
) -> Commission:
    return Commission.create(
        commission_id="com-1",
        curator_id="curator-1",
        cohort_id="cohort-1",
        module_id="module-1",
        base_amount=base_amount,
        bonus_amount=bonus_amount,
        earned_at=earned_at,
    )


# ---------------------------------------------------------------------------
# HoldPolicy value object
# ---------------------------------------------------------------------------


class TestHoldPolicy:
    def test_default_hold_days_is_30(self) -> None:
        policy = HoldPolicy()
        assert policy.hold_days == 30

    def test_custom_hold_days(self) -> None:
        policy = HoldPolicy(hold_days=7)
        assert policy.hold_days == 7

    def test_release_eligible_at_is_earned_plus_hold_days(self) -> None:
        policy = HoldPolicy(hold_days=30)
        earned_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
        eligible_at = policy.release_eligible_at(earned_at)
        assert eligible_at == datetime(2026, 1, 31, tzinfo=timezone.utc)

    def test_is_frozen(self) -> None:
        policy = HoldPolicy()
        with pytest.raises((AttributeError, TypeError)):
            policy.hold_days = 7  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Payout value object
# ---------------------------------------------------------------------------


class TestPayout:
    def test_total_is_base_plus_bonus(self) -> None:
        payout = Payout(base_amount=Decimal("80.00"), bonus_amount=Decimal("20.00"))
        assert payout.total == Decimal("100.00")

    def test_total_with_zero_bonus(self) -> None:
        payout = Payout(base_amount=Decimal("55.00"), bonus_amount=Decimal("0.00"))
        assert payout.total == Decimal("55.00")

    def test_meets_minimum_threshold_true(self) -> None:
        payout = Payout(base_amount=Decimal("50.00"), bonus_amount=Decimal("0.00"))
        assert payout.meets_minimum_threshold() is True

    def test_meets_minimum_threshold_false_below(self) -> None:
        payout = Payout(base_amount=Decimal("49.99"), bonus_amount=Decimal("0.00"))
        assert payout.meets_minimum_threshold() is False

    def test_meets_minimum_threshold_above(self) -> None:
        payout = Payout(base_amount=Decimal("100.00"), bonus_amount=Decimal("10.00"))
        assert payout.meets_minimum_threshold() is True

    def test_is_frozen(self) -> None:
        payout = Payout(base_amount=Decimal("100.00"), bonus_amount=Decimal("0.00"))
        with pytest.raises((AttributeError, TypeError)):
            payout.base_amount = Decimal("200.00")  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Commission.create factory
# ---------------------------------------------------------------------------


class TestCommissionCreate:
    def test_creates_with_correct_fields(self) -> None:
        commission = _make_commission()
        assert commission.commission_id == "com-1"
        assert commission.curator_id == "curator-1"
        assert commission.cohort_id == "cohort-1"
        assert commission.module_id == "module-1"
        assert commission.base_amount == Decimal("100.00")
        assert commission.bonus_amount == Decimal("0.00")
        assert commission.earned_at == _NOW

    def test_initial_status_is_pending(self) -> None:
        commission = _make_commission()
        assert commission.status == CommissionStatus.PENDING

    def test_release_eligible_at_is_earned_plus_30_days(self) -> None:
        commission = _make_commission(earned_at=_NOW)
        assert commission.release_eligible_at == _ELIGIBLE_AT

    def test_released_at_is_none_initially(self) -> None:
        commission = _make_commission()
        assert commission.released_at is None

    def test_emits_curation_commission_earned_event(self) -> None:
        commission = _make_commission()
        events = commission.collect_events()
        assert len(events) == 1
        event = events[0]
        assert isinstance(event, CurationCommissionEarned)
        assert event.commission_id == "com-1"
        assert event.curator_id == "curator-1"
        assert event.cohort_id == "cohort-1"
        assert event.base_amount == Decimal("100.00")
        assert event.bonus_amount == Decimal("0.00")

    def test_collect_events_clears_the_buffer(self) -> None:
        commission = _make_commission()
        commission.collect_events()  # first drain
        assert commission.collect_events() == []


# ---------------------------------------------------------------------------
# Commission.release
# ---------------------------------------------------------------------------


class TestCommissionRelease:
    def test_release_succeeds_when_eligible(self) -> None:
        commission = _make_commission(base_amount=Decimal("100.00"), earned_at=_NOW)
        commission.collect_events()  # drain creation event
        release_time = _ELIGIBLE_AT + timedelta(seconds=1)

        commission.release(now=release_time)

        assert commission.status == CommissionStatus.RELEASED
        assert commission.released_at == release_time

    def test_release_emits_payout_released_event(self) -> None:
        commission = _make_commission(base_amount=Decimal("100.00"), earned_at=_NOW)
        commission.collect_events()
        release_time = _ELIGIBLE_AT + timedelta(seconds=1)

        commission.release(now=release_time)

        events = commission.collect_events()
        assert len(events) == 1
        event = events[0]
        assert isinstance(event, PayoutReleased)
        assert event.commission_id == "com-1"
        assert event.curator_id == "curator-1"
        assert event.total_amount == Decimal("100.00")

    def test_release_raises_if_hold_period_not_elapsed(self) -> None:
        commission = _make_commission(earned_at=_NOW)
        before_eligible = _ELIGIBLE_AT - timedelta(seconds=1)

        with pytest.raises(ValueError, match="hold period"):
            commission.release(now=before_eligible)

    def test_release_raises_exactly_at_earned_at(self) -> None:
        commission = _make_commission(earned_at=_NOW)

        with pytest.raises(ValueError, match="hold period"):
            commission.release(now=_NOW)

    def test_release_succeeds_exactly_at_eligible_at(self) -> None:
        commission = _make_commission(base_amount=Decimal("100.00"), earned_at=_NOW)
        commission.collect_events()

        commission.release(now=_ELIGIBLE_AT)

        assert commission.status == CommissionStatus.RELEASED

    def test_release_raises_if_total_below_minimum_threshold(self) -> None:
        commission = _make_commission(
            base_amount=Decimal("30.00"),
            bonus_amount=Decimal("10.00"),
            earned_at=_NOW,
        )
        release_time = _ELIGIBLE_AT + timedelta(seconds=1)

        with pytest.raises(ValueError, match="minimum threshold"):
            commission.release(now=release_time)

    def test_release_succeeds_when_bonus_brings_total_to_threshold(self) -> None:
        commission = _make_commission(
            base_amount=Decimal("40.00"),
            bonus_amount=Decimal("10.00"),
            earned_at=_NOW,
        )
        commission.collect_events()
        release_time = _ELIGIBLE_AT + timedelta(seconds=1)

        commission.release(now=release_time)

        assert commission.status == CommissionStatus.RELEASED

    def test_release_raises_if_already_released(self) -> None:
        commission = _make_commission(base_amount=Decimal("100.00"), earned_at=_NOW)
        commission.collect_events()
        release_time = _ELIGIBLE_AT + timedelta(seconds=1)
        commission.release(now=release_time)
        commission.collect_events()

        with pytest.raises(ValueError, match="already released"):
            commission.release(now=release_time + timedelta(seconds=1))

    def test_released_at_stores_the_release_time(self) -> None:
        commission = _make_commission(base_amount=Decimal("100.00"), earned_at=_NOW)
        commission.collect_events()
        release_time = _ELIGIBLE_AT + timedelta(hours=2)

        commission.release(now=release_time)

        assert commission.released_at == release_time

    def test_payout_released_event_includes_total_with_bonus(self) -> None:
        commission = _make_commission(
            base_amount=Decimal("100.00"),
            bonus_amount=Decimal("5.00"),
            earned_at=_NOW,
        )
        commission.collect_events()
        release_time = _ELIGIBLE_AT + timedelta(seconds=1)

        commission.release(now=release_time)

        events = commission.collect_events()
        payout_event = events[0]
        assert isinstance(payout_event, PayoutReleased)
        assert payout_event.total_amount == Decimal("105.00")
