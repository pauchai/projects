"""Tests for GetPendingCuratorPromotionsUseCase (Stage 18).

The use case returns PendingCuratorPromotion records for a cohort,
dynamically filtering out learners who already have a ModuleCurator
record for the same (learner, module, cohort).
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from cohort_learning.application.get_pending_curator_promotions import (
    GetPendingCuratorPromotionsUseCase,
)
from cohort_learning.domain.module_curator import ModuleCurator
from cohort_learning.domain.pending_curator_promotion import PendingCuratorPromotion
from tests.cohort_learning.fakes.fake_unit_of_work import FakeUnitOfWork
from tests.cohort_learning.factories import make_active_cohort


def _make_pending(
    learner_id: str = "learner1",
    module_id: str = "mod1",
    cohort_id: str = "c1",
    pending_id: str | None = None,
) -> PendingCuratorPromotion:
    return PendingCuratorPromotion(
        pending_id=pending_id or f"p-{learner_id}-{module_id}",
        learner_id=learner_id,
        module_id=module_id,
        cohort_id=cohort_id,
        created_at=datetime.now(tz=timezone.utc),
    )


def _make_curator(
    learner_id: str = "learner1",
    module_id: str = "mod1",
    cohort_id: str = "c1",
) -> ModuleCurator:
    return ModuleCurator(
        curator_id=f"cur-{learner_id}-{module_id}",
        learner_id=learner_id,
        module_id=module_id,
        cohort_id=cohort_id,
        promoted_at=datetime.now(tz=timezone.utc),
        promoted_by="master1",
    )


class TestGetPendingCuratorPromotionsAuthorization:
    def test_master_can_query(self) -> None:
        uow = FakeUnitOfWork()
        cohort = make_active_cohort(cohort_id="c1", master_id="master1")
        with uow:
            uow.cohorts.save(cohort)
            uow.commit()

        use_case = GetPendingCuratorPromotionsUseCase(uow)
        result = use_case.execute(cohort_id="c1", caller_id="master1")
        assert isinstance(result, list)

    def test_non_master_cannot_query(self) -> None:
        uow = FakeUnitOfWork()
        cohort = make_active_cohort(cohort_id="c1", master_id="master1")
        with uow:
            uow.cohorts.save(cohort)
            uow.commit()

        use_case = GetPendingCuratorPromotionsUseCase(uow)
        with pytest.raises(PermissionError):
            use_case.execute(cohort_id="c1", caller_id="learner1")

    def test_raises_when_cohort_not_found(self) -> None:
        uow = FakeUnitOfWork()
        use_case = GetPendingCuratorPromotionsUseCase(uow)
        with pytest.raises(LookupError):
            use_case.execute(cohort_id="no-such", caller_id="master1")


class TestGetPendingCuratorPromotionsFiltering:
    def test_returns_pending_records_for_cohort(self) -> None:
        uow = FakeUnitOfWork()
        cohort = make_active_cohort(cohort_id="c1", master_id="master1")
        with uow:
            uow.cohorts.save(cohort)
            uow.pending_curator_promotions.save(_make_pending("learner1", "mod1", "c1"))
            uow.commit()

        use_case = GetPendingCuratorPromotionsUseCase(uow)
        result = use_case.execute(cohort_id="c1", caller_id="master1")
        assert len(result) == 1
        assert result[0].learner_id == "learner1"

    def test_excludes_already_promoted_learners(self) -> None:
        """Records with an existing ModuleCurator are filtered out."""
        uow = FakeUnitOfWork()
        cohort = make_active_cohort(cohort_id="c1", master_id="master1")
        with uow:
            uow.cohorts.save(cohort)
            uow.pending_curator_promotions.save(_make_pending("learner1", "mod1", "c1"))
            uow.module_curators.save(_make_curator("learner1", "mod1", "c1"))
            uow.commit()

        use_case = GetPendingCuratorPromotionsUseCase(uow)
        result = use_case.execute(cohort_id="c1", caller_id="master1")
        assert len(result) == 0

    def test_returns_empty_when_no_pending_records(self) -> None:
        uow = FakeUnitOfWork()
        cohort = make_active_cohort(cohort_id="c1", master_id="master1")
        with uow:
            uow.cohorts.save(cohort)
            uow.commit()

        use_case = GetPendingCuratorPromotionsUseCase(uow)
        result = use_case.execute(cohort_id="c1", caller_id="master1")
        assert result == []

    def test_does_not_return_records_from_other_cohorts(self) -> None:
        uow = FakeUnitOfWork()
        cohort = make_active_cohort(cohort_id="c1", master_id="master1")
        with uow:
            uow.cohorts.save(cohort)
            uow.pending_curator_promotions.save(_make_pending("learner1", "mod1", "c2"))
            uow.commit()

        use_case = GetPendingCuratorPromotionsUseCase(uow)
        result = use_case.execute(cohort_id="c1", caller_id="master1")
        assert result == []

    def test_returns_multiple_pending_records(self) -> None:
        uow = FakeUnitOfWork()
        cohort = make_active_cohort(cohort_id="c1", master_id="master1")
        with uow:
            uow.cohorts.save(cohort)
            uow.pending_curator_promotions.save(_make_pending("learner1", "mod1", "c1"))
            uow.pending_curator_promotions.save(_make_pending("learner2", "mod2", "c1"))
            uow.commit()

        use_case = GetPendingCuratorPromotionsUseCase(uow)
        result = use_case.execute(cohort_id="c1", caller_id="master1")
        assert len(result) == 2

    def test_partial_filter_keeps_unpromotd_records(self) -> None:
        """When one learner is promoted and another is not, only unpromoted shown."""
        uow = FakeUnitOfWork()
        cohort = make_active_cohort(cohort_id="c1", master_id="master1")
        with uow:
            uow.cohorts.save(cohort)
            uow.pending_curator_promotions.save(_make_pending("learner1", "mod1", "c1"))
            uow.pending_curator_promotions.save(_make_pending("learner2", "mod1", "c1"))
            uow.module_curators.save(_make_curator("learner1", "mod1", "c1"))
            uow.commit()

        use_case = GetPendingCuratorPromotionsUseCase(uow)
        result = use_case.execute(cohort_id="c1", caller_id="master1")
        assert len(result) == 1
        assert result[0].learner_id == "learner2"
