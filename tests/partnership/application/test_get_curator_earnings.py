"""Tests for GetCuratorEarningsUseCase (Stage 11 — RED phase)."""

from __future__ import annotations

from decimal import Decimal
from datetime import datetime, timezone

from partnership.application.get_curator_earnings import GetCuratorEarningsUseCase
from partnership.domain.commission import Commission
from tests.partnership.fakes.fake_unit_of_work import FakeUnitOfWork

_NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _make_commission(commission_id: str, curator_id: str) -> Commission:
    c = Commission.create(
        commission_id=commission_id,
        curator_id=curator_id,
        cohort_id="cohort-1",
        module_id="module-1",
        base_amount=Decimal("100.00"),
        bonus_amount=Decimal("0.00"),
        earned_at=_NOW,
    )
    c.collect_events()
    return c


class TestGetCuratorEarningsUseCase:
    def test_returns_empty_list_when_no_commissions(self) -> None:
        uow = FakeUnitOfWork()
        uc = GetCuratorEarningsUseCase(uow)

        result = uc.execute(curator_id="curator-1")

        assert result == []

    def test_returns_commissions_for_given_curator(self) -> None:
        uow = FakeUnitOfWork()
        c1 = _make_commission("com-1", "curator-1")
        c2 = _make_commission("com-2", "curator-1")
        uow.commissions._storage["com-1"] = c1
        uow.commissions._storage["com-2"] = c2
        uc = GetCuratorEarningsUseCase(uow)

        result = uc.execute(curator_id="curator-1")

        assert len(result) == 2
        ids = {c.commission_id for c in result}
        assert ids == {"com-1", "com-2"}

    def test_does_not_return_other_curators_commissions(self) -> None:
        uow = FakeUnitOfWork()
        c1 = _make_commission("com-1", "curator-1")
        c2 = _make_commission("com-2", "curator-2")
        uow.commissions._storage["com-1"] = c1
        uow.commissions._storage["com-2"] = c2
        uc = GetCuratorEarningsUseCase(uow)

        result = uc.execute(curator_id="curator-1")

        assert len(result) == 1
        assert result[0].commission_id == "com-1"
