"""Tests for RecordHelperActivity use case."""

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from cohort_learning.application.record_helper_activity import (
    RecordHelperActivityUseCase,
)
from cohort_learning.domain.helper_metrics import HelperMetrics
from tests.cohort_learning.fakes.fake_unit_of_work import FakeUnitOfWork
from tests.cohort_learning.factories import make_active_cohort, save_cohort


class TestRecordHelperActivityUseCase:
    """Record helper activity (peer reviews, learners helped)."""

    def test_records_first_peer_review(self) -> None:
        """When recording first peer review, creates HelperMetrics with review count 1."""
        uow = FakeUnitOfWork()
        cohort = make_active_cohort()
        save_cohort(uow, cohort)

        use_case = RecordHelperActivityUseCase(uow=uow)

        use_case.execute(
            learner_id="learner1",
            cohort_id="c1",
            activity_type="peer_review",
            satisfaction_score=Decimal("4.5"),
        )

        metrics = uow.helper_metrics.find_by_learner("learner1", "c1")
        assert metrics is not None
        assert metrics.tasks_reviewed == 1
        assert metrics.average_satisfaction == Decimal("4.5")

    def test_records_subsequent_peer_review(self) -> None:
        """When recording additional review, updates tasks_reviewed and recalculates average."""
        uow = FakeUnitOfWork()
        cohort = make_active_cohort()
        save_cohort(uow, cohort)

        # Create initial metrics
        initial_metrics = HelperMetrics(
            learner_id="learner1",
            cohort_id="c1",
            learners_helped=0,
            questions_answered=0,
            tasks_reviewed=2,
            average_satisfaction=Decimal("4.0"),
            updated_at=datetime.now(timezone.utc),
        )
        with uow:
            uow.helper_metrics.save(initial_metrics)
            uow.commit()

        use_case = RecordHelperActivityUseCase(uow=uow)

        use_case.execute(
            learner_id="learner1",
            cohort_id="c1",
            activity_type="peer_review",
            satisfaction_score=Decimal("5.0"),
        )

        metrics = uow.helper_metrics.find_by_learner("learner1", "c1")
        assert metrics is not None
        assert metrics.tasks_reviewed == 3
        # Average: (4.0 * 2 + 5.0) / 3 = 13 / 3 = 4.333...
        expected_avg = (Decimal("4.0") * 2 + Decimal("5.0")) / 3
        assert abs(metrics.average_satisfaction - expected_avg) < Decimal("0.001")

    def test_records_first_learner_helped(self) -> None:
        """When recording first learner helped, creates HelperMetrics with count 1."""
        uow = FakeUnitOfWork()
        cohort = make_active_cohort()
        save_cohort(uow, cohort)

        use_case = RecordHelperActivityUseCase(uow=uow)

        use_case.execute(
            learner_id="learner1",
            cohort_id="c1",
            activity_type="learner_helped",
            helped_learner_id="learner2",
        )

        metrics = uow.helper_metrics.find_by_learner("learner1", "c1")
        assert metrics is not None
        assert metrics.learners_helped == 1

    def test_records_subsequent_learner_helped(self) -> None:
        """When recording additional learner helped, increments counter."""
        uow = FakeUnitOfWork()
        cohort = make_active_cohort()
        save_cohort(uow, cohort)

        # Create initial metrics
        initial_metrics = HelperMetrics(
            learner_id="learner1",
            cohort_id="c1",
            learners_helped=2,
            questions_answered=0,
            tasks_reviewed=0,
            average_satisfaction=None,
            updated_at=datetime.now(timezone.utc),
        )
        with uow:
            uow.helper_metrics.save(initial_metrics)
            uow.commit()

        use_case = RecordHelperActivityUseCase(uow=uow)

        use_case.execute(
            learner_id="learner1",
            cohort_id="c1",
            activity_type="learner_helped",
            helped_learner_id="learner3",
        )

        metrics = uow.helper_metrics.find_by_learner("learner1", "c1")
        assert metrics is not None
        assert metrics.learners_helped == 3

    def test_raises_when_cohort_not_found(self) -> None:
        """Activity recording fails if cohort doesn't exist."""
        uow = FakeUnitOfWork()
        use_case = RecordHelperActivityUseCase(uow=uow)

        with pytest.raises(LookupError, match="Cohort.*not found"):
            use_case.execute(
                learner_id="learner1",
                cohort_id="nonexistent",
                activity_type="peer_review",
                satisfaction_score=Decimal("4.0"),
            )

    def test_raises_when_invalid_activity_type(self) -> None:
        """Raises ValueError for unknown activity type."""
        uow = FakeUnitOfWork()
        cohort = make_active_cohort()
        save_cohort(uow, cohort)

        use_case = RecordHelperActivityUseCase(uow=uow)

        with pytest.raises(ValueError, match="Invalid activity_type"):
            use_case.execute(
                learner_id="learner1",
                cohort_id="c1",
                activity_type="invalid_type",
            )

    def test_commits_transaction(self) -> None:
        """Use case commits the transaction after recording."""
        uow = FakeUnitOfWork()
        cohort = make_active_cohort()
        save_cohort(uow, cohort)

        use_case = RecordHelperActivityUseCase(uow=uow)

        use_case.execute(
            learner_id="learner1",
            cohort_id="c1",
            activity_type="peer_review",
            satisfaction_score=Decimal("4.0"),
        )

        assert uow.committed is True
