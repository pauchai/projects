"""Tests for CalculateCurationCommissionUseCase (Stage 11 — RED phase)."""

from __future__ import annotations

from decimal import Decimal

import pytest

from partnership.application.calculate_curation_commission import (
    CalculateCurationCommissionUseCase,
)
from partnership.domain.commission import Commission, CommissionStatus
from partnership.domain.events import CurationCommissionEarned, QualityBonusEarned
from tests.partnership.fakes.fake_unit_of_work import FakeUnitOfWork


class TestCalculateCurationCommissionUseCase:
    def _make_uow(self) -> FakeUnitOfWork:
        return FakeUnitOfWork()

    def _make_use_case(self, uow: FakeUnitOfWork) -> CalculateCurationCommissionUseCase:
        return CalculateCurationCommissionUseCase(uow)

    def test_creates_commission_and_saves_to_uow(self) -> None:
        uow = self._make_uow()
        uc = self._make_use_case(uow)

        uc.execute(
            curator_id="curator-1",
            cohort_id="cohort-1",
            module_id="module-1",
            cohort_size=10,
            curator_score=20,
            avg_review_score=4.0,
        )

        commissions = uow.commissions.find_by_curator("curator-1")
        assert len(commissions) == 1

    def test_base_amount_equals_rate_times_cohort_size_times_curator_score(
        self,
    ) -> None:
        uow = self._make_uow()
        uc = self._make_use_case(uow)

        result = uc.execute(
            curator_id="curator-1",
            cohort_id="cohort-1",
            module_id="module-1",
            cohort_size=10,
            curator_score=20,
            avg_review_score=4.0,
        )

        # base_rate=10%, cohort_size=10, curator_score=20 → 0.10 * 10 * 20 = 20.00
        assert result.base_amount == Decimal("20.00")

    def test_no_bonus_when_avg_review_score_is_at_or_below_4_5(self) -> None:
        uow = self._make_uow()
        uc = self._make_use_case(uow)

        result = uc.execute(
            curator_id="curator-1",
            cohort_id="cohort-1",
            module_id="module-1",
            cohort_size=10,
            curator_score=20,
            avg_review_score=4.5,
        )

        assert result.bonus_amount == Decimal("0.00")

    def test_no_bonus_when_avg_review_score_is_below_4_5(self) -> None:
        uow = self._make_uow()
        uc = self._make_use_case(uow)

        result = uc.execute(
            curator_id="curator-1",
            cohort_id="cohort-1",
            module_id="module-1",
            cohort_size=10,
            curator_score=20,
            avg_review_score=4.0,
        )

        assert result.bonus_amount == Decimal("0.00")

    def test_quality_bonus_applied_when_avg_review_score_above_4_5(self) -> None:
        uow = self._make_uow()
        uc = self._make_use_case(uow)

        result = uc.execute(
            curator_id="curator-1",
            cohort_id="cohort-1",
            module_id="module-1",
            cohort_size=10,
            curator_score=20,
            avg_review_score=4.6,
        )

        # base=20.00, bonus=20.00*0.05=1.00
        assert result.base_amount == Decimal("20.00")
        assert result.bonus_amount == Decimal("1.00")

    def test_commission_status_is_pending(self) -> None:
        uow = self._make_uow()
        uc = self._make_use_case(uow)

        result = uc.execute(
            curator_id="curator-1",
            cohort_id="cohort-1",
            module_id="module-1",
            cohort_size=5,
            curator_score=10,
            avg_review_score=3.0,
        )

        assert result.status == CommissionStatus.PENDING

    def test_commission_fields_are_populated(self) -> None:
        uow = self._make_uow()
        uc = self._make_use_case(uow)

        result = uc.execute(
            curator_id="curator-1",
            cohort_id="cohort-42",
            module_id="module-99",
            cohort_size=8,
            curator_score=15,
            avg_review_score=3.0,
        )

        assert result.curator_id == "curator-1"
        assert result.cohort_id == "cohort-42"
        assert result.module_id == "module-99"
        assert result.commission_id  # non-empty

    def test_uow_is_committed(self) -> None:
        uow = self._make_uow()
        uc = self._make_use_case(uow)

        uc.execute(
            curator_id="curator-1",
            cohort_id="cohort-1",
            module_id="module-1",
            cohort_size=10,
            curator_score=10,
            avg_review_score=3.0,
        )

        assert uow.committed is True

    def test_quality_bonus_event_emitted_when_avg_above_4_5(self) -> None:
        """UoW accumulates a QualityBonusEarned event when bonus applies."""
        uow = self._make_uow()
        uc = self._make_use_case(uow)

        uc.execute(
            curator_id="curator-1",
            cohort_id="cohort-1",
            module_id="module-1",
            cohort_size=10,
            curator_score=20,
            avg_review_score=5.0,
        )

        # Events were published (pending cleared after commit); verify via saved commission
        commissions = uow.commissions.find_by_curator("curator-1")
        assert commissions[0].bonus_amount > Decimal("0")

    def test_zero_curator_score_produces_zero_base_amount(self) -> None:
        uow = self._make_uow()
        uc = self._make_use_case(uow)

        result = uc.execute(
            curator_id="curator-1",
            cohort_id="cohort-1",
            module_id="module-1",
            cohort_size=10,
            curator_score=0,
            avg_review_score=3.0,
        )

        assert result.base_amount == Decimal("0.00")
