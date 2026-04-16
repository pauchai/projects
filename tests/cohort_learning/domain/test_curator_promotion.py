"""Tests for CuratorPromotionService domain service."""

import pytest
from datetime import datetime, UTC
from decimal import Decimal

from cohort_learning.domain.curator_promotion import (
    CuratorPromotionService,
    PromotionRequirement,
    PromotionResult,
)
from cohort_learning.domain.helper_metrics import HelperMetrics


class TestCuratorPromotionRequirements:
    def test_promotion_succeeds_when_all_requirements_met(self) -> None:
        # Arrange
        service = CuratorPromotionService()
        metrics = HelperMetrics(
            learner_id="learner-1",
            cohort_id="cohort-1",
            learners_helped=3,
            questions_answered=10,
            tasks_reviewed=5,
            average_satisfaction=Decimal("4.0"),
            updated_at=datetime(2026, 4, 15, 10, 0, 0, tzinfo=UTC),
        )

        # Act
        result = service.evaluate_promotion(
            learner_id="learner-1",
            module_id="module-frontend",
            helper_metrics=metrics,
            module_completed=True,
            teaching_trial_passed=True,
            master_approved=True,
        )

        # Assert
        assert result.is_approved is True
        assert result.failed_requirements == []

    def test_promotion_fails_if_module_not_completed(self) -> None:
        # Arrange
        service = CuratorPromotionService()
        metrics = HelperMetrics(
            learner_id="learner-1",
            cohort_id="cohort-1",
            learners_helped=3,
            questions_answered=10,
            tasks_reviewed=5,
            average_satisfaction=Decimal("4.5"),
            updated_at=datetime(2026, 4, 15, 10, 0, 0, tzinfo=UTC),
        )

        # Act
        result = service.evaluate_promotion(
            learner_id="learner-1",
            module_id="module-frontend",
            helper_metrics=metrics,
            module_completed=False,  # FAIL
            teaching_trial_passed=True,
            master_approved=True,
        )

        # Assert
        assert result.is_approved is False
        assert PromotionRequirement.MODULE_COMPLETION in result.failed_requirements

    def test_promotion_fails_if_helper_metrics_below_threshold(self) -> None:
        # Arrange
        service = CuratorPromotionService()
        metrics = HelperMetrics(
            learner_id="learner-1",
            cohort_id="cohort-1",
            learners_helped=2,  # < 3
            questions_answered=10,
            tasks_reviewed=5,
            average_satisfaction=Decimal("4.5"),
            updated_at=datetime(2026, 4, 15, 10, 0, 0, tzinfo=UTC),
        )

        # Act
        result = service.evaluate_promotion(
            learner_id="learner-1",
            module_id="module-frontend",
            helper_metrics=metrics,
            module_completed=True,
            teaching_trial_passed=True,
            master_approved=True,
        )

        # Assert
        assert result.is_approved is False
        assert PromotionRequirement.HELPER_TRACK_RECORD in result.failed_requirements

    def test_promotion_fails_if_teaching_trial_not_passed(self) -> None:
        # Arrange
        service = CuratorPromotionService()
        metrics = HelperMetrics(
            learner_id="learner-1",
            cohort_id="cohort-1",
            learners_helped=5,
            questions_answered=10,
            tasks_reviewed=10,
            average_satisfaction=Decimal("4.5"),
            updated_at=datetime(2026, 4, 15, 10, 0, 0, tzinfo=UTC),
        )

        # Act
        result = service.evaluate_promotion(
            learner_id="learner-1",
            module_id="module-frontend",
            helper_metrics=metrics,
            module_completed=True,
            teaching_trial_passed=False,  # FAIL
            master_approved=True,
        )

        # Assert
        assert result.is_approved is False
        assert PromotionRequirement.TEACHING_TRIAL in result.failed_requirements

    def test_promotion_fails_if_master_not_approved(self) -> None:
        # Arrange
        service = CuratorPromotionService()
        metrics = HelperMetrics(
            learner_id="learner-1",
            cohort_id="cohort-1",
            learners_helped=5,
            questions_answered=10,
            tasks_reviewed=10,
            average_satisfaction=Decimal("4.5"),
            updated_at=datetime(2026, 4, 15, 10, 0, 0, tzinfo=UTC),
        )

        # Act
        result = service.evaluate_promotion(
            learner_id="learner-1",
            module_id="module-frontend",
            helper_metrics=metrics,
            module_completed=True,
            teaching_trial_passed=True,
            master_approved=False,  # FAIL
        )

        # Assert
        assert result.is_approved is False
        assert PromotionRequirement.MASTER_APPROVAL in result.failed_requirements

    def test_promotion_can_fail_multiple_requirements(self) -> None:
        # Arrange
        service = CuratorPromotionService()
        metrics = HelperMetrics(
            learner_id="learner-1",
            cohort_id="cohort-1",
            learners_helped=1,  # FAIL
            questions_answered=2,
            tasks_reviewed=2,  # FAIL
            average_satisfaction=None,  # FAIL
            updated_at=datetime(2026, 4, 15, 10, 0, 0, tzinfo=UTC),
        )

        # Act
        result = service.evaluate_promotion(
            learner_id="learner-1",
            module_id="module-frontend",
            helper_metrics=metrics,
            module_completed=False,  # FAIL
            teaching_trial_passed=False,  # FAIL
            master_approved=True,
        )

        # Assert
        assert result.is_approved is False
        assert len(result.failed_requirements) >= 3
        assert PromotionRequirement.MODULE_COMPLETION in result.failed_requirements
        assert PromotionRequirement.HELPER_TRACK_RECORD in result.failed_requirements
        assert PromotionRequirement.TEACHING_TRIAL in result.failed_requirements


class TestPromotionResultFeedback:
    def test_promotion_result_provides_feedback_for_failures(self) -> None:
        # Arrange
        service = CuratorPromotionService()
        metrics = HelperMetrics(
            learner_id="learner-1",
            cohort_id="cohort-1",
            learners_helped=1,
            questions_answered=2,
            tasks_reviewed=2,
            average_satisfaction=None,
            updated_at=datetime(2026, 4, 15, 10, 0, 0, tzinfo=UTC),
        )

        # Act
        result = service.evaluate_promotion(
            learner_id="learner-1",
            module_id="module-frontend",
            helper_metrics=metrics,
            module_completed=False,
            teaching_trial_passed=True,
            master_approved=True,
        )

        # Assert
        feedback = result.get_feedback()
        assert "module" in feedback.lower()
        assert "helper" in feedback.lower() or "helped" in feedback.lower()
