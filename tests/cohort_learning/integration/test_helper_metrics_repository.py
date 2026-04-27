"""Integration tests for SqlAlchemyHelperMetricsRepository.

Tests verify that HelperMetrics entities can be saved to and loaded from
a real PostgreSQL database, with proper Decimal ↔ String conversion for
average_satisfaction. The table uses a composite primary key (learner_id, cohort_id).
"""

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from cohort_learning.domain.helper_metrics import HelperMetrics
from cohort_learning.infrastructure.sqlalchemy_repository import (
    SqlAlchemyHelperMetricsRepository,
)


@pytest.fixture
def repo(integration_session):
    """Provide a HelperMetrics repository backed by a real database session."""
    return SqlAlchemyHelperMetricsRepository(integration_session)


class TestSqlAlchemyHelperMetricsRepository:
    """Integration tests for HelperMetrics persistence."""

    def test_save_and_find_by_learner_and_cohort_round_trip(self, repo):
        """Saving and retrieving HelperMetrics preserves all fields."""
        # Arrange
        metrics = HelperMetrics(
            learner_id="learner-1",
            cohort_id="cohort-1",
            learners_helped=5,
            questions_answered=12,
            tasks_reviewed=8,
            average_satisfaction=Decimal("4.75"),
            updated_at=datetime(2026, 4, 15, 12, 0, 0, tzinfo=timezone.utc),
        )

        # Act
        repo.save(metrics)
        found = repo.find_by_learner_and_cohort("learner-1", "cohort-1")

        # Assert
        assert found is not None
        assert found.learner_id == "learner-1"
        assert found.cohort_id == "cohort-1"
        assert found.learners_helped == 5
        assert found.questions_answered == 12
        assert found.tasks_reviewed == 8
        assert found.average_satisfaction == Decimal("4.75")
        assert found.updated_at == datetime(2026, 4, 15, 12, 0, 0, tzinfo=timezone.utc)

    def test_find_by_learner_and_cohort_returns_none_when_not_found(self, repo):
        """Finding non-existent HelperMetrics returns None."""
        # Act
        found = repo.find_by_learner_and_cohort("nonexistent", "cohort-99")

        # Assert
        assert found is None

    def test_save_with_null_average_satisfaction(self, repo):
        """HelperMetrics can be saved with null average_satisfaction."""
        # Arrange
        metrics = HelperMetrics(
            learner_id="learner-2",
            cohort_id="cohort-2",
            learners_helped=0,
            questions_answered=0,
            tasks_reviewed=0,
            average_satisfaction=None,
            updated_at=datetime(2026, 4, 15, 12, 0, 0, tzinfo=timezone.utc),
        )

        # Act
        repo.save(metrics)
        found = repo.find_by_learner_and_cohort("learner-2", "cohort-2")

        # Assert
        assert found is not None
        assert found.average_satisfaction is None

    def test_save_updates_existing_metrics(self, repo):
        """Saving HelperMetrics with same composite key updates the record."""
        # Arrange
        metrics_v1 = HelperMetrics(
            learner_id="learner-3",
            cohort_id="cohort-3",
            learners_helped=1,
            questions_answered=2,
            tasks_reviewed=1,
            average_satisfaction=Decimal("3.00"),
            updated_at=datetime(2026, 4, 15, 12, 0, 0, tzinfo=timezone.utc),
        )
        repo.save(metrics_v1)

        # Act — save updated metrics with same composite key
        metrics_v2 = HelperMetrics(
            learner_id="learner-3",
            cohort_id="cohort-3",
            learners_helped=5,
            questions_answered=10,
            tasks_reviewed=7,
            average_satisfaction=Decimal("4.50"),
            updated_at=datetime(2026, 4, 15, 14, 0, 0, tzinfo=timezone.utc),
        )
        repo.save(metrics_v2)

        # Assert — only one record exists, with updated values
        found = repo.find_by_learner_and_cohort("learner-3", "cohort-3")
        assert found is not None
        assert found.learners_helped == 5
        assert found.questions_answered == 10
        assert found.tasks_reviewed == 7
        assert found.average_satisfaction == Decimal("4.50")

    def test_find_by_cohort(self, repo):
        """Can find all HelperMetrics for a cohort."""
        # Arrange
        metrics1 = HelperMetrics(
            learner_id="learner-4",
            cohort_id="cohort-4",
            learners_helped=3,
            questions_answered=5,
            tasks_reviewed=2,
            average_satisfaction=Decimal("4.00"),
            updated_at=datetime(2026, 4, 15, 12, 0, 0, tzinfo=timezone.utc),
        )
        metrics2 = HelperMetrics(
            learner_id="learner-5",
            cohort_id="cohort-4",
            learners_helped=7,
            questions_answered=15,
            tasks_reviewed=10,
            average_satisfaction=Decimal("4.80"),
            updated_at=datetime(2026, 4, 15, 13, 0, 0, tzinfo=timezone.utc),
        )
        metrics3 = HelperMetrics(
            learner_id="learner-6",
            cohort_id="cohort-999",  # different cohort
            learners_helped=1,
            questions_answered=2,
            tasks_reviewed=1,
            average_satisfaction=Decimal("3.50"),
            updated_at=datetime(2026, 4, 15, 14, 0, 0, tzinfo=timezone.utc),
        )
        repo.save(metrics1)
        repo.save(metrics2)
        repo.save(metrics3)

        # Act
        metrics = repo.find_by_cohort("cohort-4")

        # Assert
        assert len(metrics) == 2
        learner_ids = {m.learner_id for m in metrics}
        assert learner_ids == {"learner-4", "learner-5"}

    def test_decimal_precision_preserved(self, repo):
        """Decimal values are preserved with correct precision after round trip."""
        # Arrange
        metrics = HelperMetrics(
            learner_id="learner-7",
            cohort_id="cohort-7",
            learners_helped=10,
            questions_answered=25,
            tasks_reviewed=15,
            average_satisfaction=Decimal("4.123456"),  # high precision
            updated_at=datetime(2026, 4, 15, 12, 0, 0, tzinfo=timezone.utc),
        )

        # Act
        repo.save(metrics)
        found = repo.find_by_learner_and_cohort("learner-7", "cohort-7")

        # Assert
        assert found is not None
        # String column is limited to 10 chars, so precision might be limited
        # but the Decimal conversion should work correctly
        assert isinstance(found.average_satisfaction, Decimal)
        assert str(found.average_satisfaction) == "4.123456"
