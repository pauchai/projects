"""Tests for GetHelperMetrics use case."""

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from cohort_learning.application.get_helper_metrics import GetHelperMetricsUseCase
from cohort_learning.domain.helper_metrics import HelperMetrics
from tests.cohort_learning.fakes.fake_unit_of_work import FakeUnitOfWork
from tests.cohort_learning.factories import make_active_cohort, save_cohort


class TestGetHelperMetricsUseCase:
    """Get helper metrics for a learner in a cohort."""

    def test_returns_existing_helper_metrics(self) -> None:
        """When metrics exist, returns them."""
        uow = FakeUnitOfWork()
        cohort = make_active_cohort()
        save_cohort(uow, cohort)

        # Create helper metrics
        metrics = HelperMetrics(
            learner_id="learner1",
            cohort_id="c1",
            learners_helped=3,
            questions_answered=5,
            tasks_reviewed=7,
            average_satisfaction=Decimal("4.2"),
            updated_at=datetime.now(timezone.utc),
        )
        with uow:
            uow.helper_metrics.save(metrics)
            uow.commit()

        use_case = GetHelperMetricsUseCase(uow=uow)

        result = use_case.execute(
            learner_id="learner1",
            cohort_id="c1",
            caller_id="master1",
        )

        assert result is not None
        assert result.learner_id == "learner1"
        assert result.learners_helped == 3
        assert result.tasks_reviewed == 7

    def test_returns_none_when_no_metrics_exist(self) -> None:
        """When learner has no helper metrics, returns None."""
        uow = FakeUnitOfWork()
        cohort = make_active_cohort()
        save_cohort(uow, cohort)

        use_case = GetHelperMetricsUseCase(uow=uow)

        result = use_case.execute(
            learner_id="learner1",
            cohort_id="c1",
            caller_id="master1",
        )

        assert result is None

    def test_allows_learner_to_view_own_metrics(self) -> None:
        """Learner can view their own helper metrics."""
        uow = FakeUnitOfWork()
        cohort = make_active_cohort()
        save_cohort(uow, cohort)

        # Create helper metrics
        metrics = HelperMetrics(
            learner_id="learner1",
            cohort_id="c1",
            learners_helped=2,
            questions_answered=3,
            tasks_reviewed=4,
            average_satisfaction=Decimal("3.8"),
            updated_at=datetime.now(timezone.utc),
        )
        with uow:
            uow.helper_metrics.save(metrics)
            uow.commit()

        use_case = GetHelperMetricsUseCase(uow=uow)

        result = use_case.execute(
            learner_id="learner1",
            cohort_id="c1",
            caller_id="learner1",  # Same as learner_id
        )

        assert result is not None
        assert result.learner_id == "learner1"

    def test_allows_cohort_member_to_view_others_metrics(self) -> None:
        """Any cohort member can view other members' helper metrics."""
        uow = FakeUnitOfWork()
        cohort = make_active_cohort()
        save_cohort(uow, cohort)

        # Create helper metrics
        metrics = HelperMetrics(
            learner_id="learner1",
            cohort_id="c1",
            learners_helped=1,
            questions_answered=2,
            tasks_reviewed=3,
            average_satisfaction=Decimal("4.0"),
            updated_at=datetime.now(timezone.utc),
        )
        with uow:
            uow.helper_metrics.save(metrics)
            uow.commit()

        use_case = GetHelperMetricsUseCase(uow=uow)

        result = use_case.execute(
            learner_id="learner1",
            cohort_id="c1",
            caller_id="learner2",  # Different member
        )

        assert result is not None
        assert result.learner_id == "learner1"

    def test_raises_when_caller_not_cohort_member(self) -> None:
        """Non-members cannot view helper metrics."""
        uow = FakeUnitOfWork()
        cohort = make_active_cohort()
        save_cohort(uow, cohort)

        use_case = GetHelperMetricsUseCase(uow=uow)

        with pytest.raises(PermissionError, match="not an active member"):
            use_case.execute(
                learner_id="learner1",
                cohort_id="c1",
                caller_id="outsider",  # Not a member
            )

    def test_raises_when_cohort_not_found(self) -> None:
        """Viewing metrics fails if cohort doesn't exist."""
        uow = FakeUnitOfWork()
        use_case = GetHelperMetricsUseCase(uow=uow)

        with pytest.raises(LookupError, match="Cohort.*not found"):
            use_case.execute(
                learner_id="learner1",
                cohort_id="nonexistent",
                caller_id="master1",
            )

    def test_commits_transaction(self) -> None:
        """Use case commits the transaction (read-only, but follows pattern)."""
        uow = FakeUnitOfWork()
        cohort = make_active_cohort()
        save_cohort(uow, cohort)

        use_case = GetHelperMetricsUseCase(uow=uow)

        use_case.execute(
            learner_id="learner1",
            cohort_id="c1",
            caller_id="master1",
        )

        assert uow.committed is True
