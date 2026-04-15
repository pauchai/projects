"""Tests for HelperMetrics value object."""

import pytest
from datetime import datetime, UTC
from decimal import Decimal

from cohort_learning.domain.helper_metrics import HelperMetrics


class TestHelperMetricsCreation:
    def test_create_metrics_with_zero_activity(self) -> None:
        # Arrange & Act
        metrics = HelperMetrics(
            learner_id="learner-1",
            cohort_id="cohort-1",
            learners_helped=0,
            questions_answered=0,
            tasks_reviewed=0,
            average_satisfaction=None,
            updated_at=datetime(2026, 4, 15, 10, 0, 0, tzinfo=UTC),
        )

        # Assert
        assert metrics.learner_id == "learner-1"
        assert metrics.learners_helped == 0
        assert metrics.questions_answered == 0
        assert metrics.tasks_reviewed == 0
        assert metrics.average_satisfaction is None
        assert metrics.updated_at == datetime(2026, 4, 15, 10, 0, 0, tzinfo=UTC)

    def test_create_metrics_with_activity(self) -> None:
        # Arrange & Act
        metrics = HelperMetrics(
            learner_id="learner-1",
            cohort_id="cohort-1",
            learners_helped=5,
            questions_answered=12,
            tasks_reviewed=8,
            average_satisfaction=Decimal("4.5"),
            updated_at=datetime(2026, 4, 15, 10, 0, 0, tzinfo=UTC),
        )

        # Assert
        assert metrics.learners_helped == 5
        assert metrics.questions_answered == 12
        assert metrics.tasks_reviewed == 8
        assert metrics.average_satisfaction == Decimal("4.5")


class TestHelperMetricsIncrements:
    def test_record_peer_review_increments_tasks_reviewed(self) -> None:
        # Arrange
        metrics = HelperMetrics(
            learner_id="learner-1",
            cohort_id="cohort-1",
            learners_helped=0,
            questions_answered=0,
            tasks_reviewed=0,
            average_satisfaction=None,
            updated_at=datetime(2026, 4, 15, 10, 0, 0, tzinfo=UTC),
        )

        # Act
        updated = metrics.record_peer_review(
            satisfaction_score=Decimal("4.0"),
            timestamp=datetime(2026, 4, 15, 11, 0, 0, tzinfo=UTC),
        )

        # Assert
        assert updated.tasks_reviewed == 1
        assert updated.average_satisfaction == Decimal("4.0")
        assert updated.updated_at == datetime(2026, 4, 15, 11, 0, 0, tzinfo=UTC)
        # Original is immutable
        assert metrics.tasks_reviewed == 0

    def test_record_multiple_reviews_calculates_average_satisfaction(self) -> None:
        # Arrange
        metrics = HelperMetrics(
            learner_id="learner-1",
            cohort_id="cohort-1",
            learners_helped=0,
            questions_answered=0,
            tasks_reviewed=0,
            average_satisfaction=None,
            updated_at=datetime(2026, 4, 15, 10, 0, 0, tzinfo=UTC),
        )

        # Act — record 3 reviews with scores 4.0, 5.0, 3.0
        after_first = metrics.record_peer_review(
            satisfaction_score=Decimal("4.0"),
            timestamp=datetime(2026, 4, 15, 11, 0, 0, tzinfo=UTC),
        )
        after_second = after_first.record_peer_review(
            satisfaction_score=Decimal("5.0"),
            timestamp=datetime(2026, 4, 15, 12, 0, 0, tzinfo=UTC),
        )
        after_third = after_second.record_peer_review(
            satisfaction_score=Decimal("3.0"),
            timestamp=datetime(2026, 4, 15, 13, 0, 0, tzinfo=UTC),
        )

        # Assert — average = (4.0 + 5.0 + 3.0) / 3 = 4.0
        assert after_third.tasks_reviewed == 3
        assert after_third.average_satisfaction == Decimal("4.0")

    def test_record_learner_helped_increments_count(self) -> None:
        # Arrange
        metrics = HelperMetrics(
            learner_id="learner-1",
            cohort_id="cohort-1",
            learners_helped=0,
            questions_answered=0,
            tasks_reviewed=0,
            average_satisfaction=None,
            updated_at=datetime(2026, 4, 15, 10, 0, 0, tzinfo=UTC),
        )

        # Act
        updated = metrics.record_learner_helped(
            helped_learner_id="learner-2",
            timestamp=datetime(2026, 4, 15, 11, 0, 0, tzinfo=UTC),
        )

        # Assert
        assert updated.learners_helped == 1
        assert updated.updated_at == datetime(2026, 4, 15, 11, 0, 0, tzinfo=UTC)


class TestHelperMetricsQualification:
    def test_meets_curator_threshold_when_all_criteria_met(self) -> None:
        # Arrange — threshold: ≥3 learners helped, ≥5 tasks reviewed, ≥4.0 satisfaction
        metrics = HelperMetrics(
            learner_id="learner-1",
            cohort_id="cohort-1",
            learners_helped=3,
            questions_answered=10,
            tasks_reviewed=5,
            average_satisfaction=Decimal("4.0"),
            updated_at=datetime(2026, 4, 15, 10, 0, 0, tzinfo=UTC),
        )

        # Act & Assert
        assert metrics.meets_curator_threshold() is True

    def test_does_not_meet_threshold_with_insufficient_learners_helped(self) -> None:
        # Arrange
        metrics = HelperMetrics(
            learner_id="learner-1",
            cohort_id="cohort-1",
            learners_helped=2,  # < 3
            questions_answered=10,
            tasks_reviewed=5,
            average_satisfaction=Decimal("4.5"),
            updated_at=datetime(2026, 4, 15, 10, 0, 0, tzinfo=UTC),
        )

        # Act & Assert
        assert metrics.meets_curator_threshold() is False

    def test_does_not_meet_threshold_with_low_satisfaction(self) -> None:
        # Arrange
        metrics = HelperMetrics(
            learner_id="learner-1",
            cohort_id="cohort-1",
            learners_helped=5,
            questions_answered=10,
            tasks_reviewed=10,
            average_satisfaction=Decimal("3.9"),  # < 4.0
            updated_at=datetime(2026, 4, 15, 10, 0, 0, tzinfo=UTC),
        )

        # Act & Assert
        assert metrics.meets_curator_threshold() is False

    def test_does_not_meet_threshold_with_no_satisfaction_data(self) -> None:
        # Arrange
        metrics = HelperMetrics(
            learner_id="learner-1",
            cohort_id="cohort-1",
            learners_helped=5,
            questions_answered=10,
            tasks_reviewed=10,
            average_satisfaction=None,  # no reviews yet
            updated_at=datetime(2026, 4, 15, 10, 0, 0, tzinfo=UTC),
        )

        # Act & Assert
        assert metrics.meets_curator_threshold() is False
