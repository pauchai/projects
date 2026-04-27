"""Tests for CompetencyValidation domain service."""

import pytest
from datetime import datetime, UTC

from cohort_learning.domain.competency_validation import (
    CompetencyValidation,
    ValidationStep,
    ValidationResult,
)


class TestCompetencyValidationSteps:
    def test_all_steps_must_pass_for_successful_validation(self) -> None:
        # Arrange
        validation = CompetencyValidation(
            learner_id="learner-1",
            topic_id="topic-react-hooks",
            cohort_id="cohort-1",
        )

        # Act
        result = validation.validate(
            tasks_completed=True,
            knowledge_check_score=75,  # ≥ 70%
            peer_review_received=True,
            mentor_approved=True,
        )

        # Assert
        assert result.is_valid is True
        assert result.failed_steps == []

    def test_validation_fails_if_tasks_not_completed(self) -> None:
        # Arrange
        validation = CompetencyValidation(
            learner_id="learner-1",
            topic_id="topic-react-hooks",
            cohort_id="cohort-1",
        )

        # Act
        result = validation.validate(
            tasks_completed=False,  # FAIL
            knowledge_check_score=80,
            peer_review_received=True,
            mentor_approved=True,
        )

        # Assert
        assert result.is_valid is False
        assert ValidationStep.TASK_COMPLETION in result.failed_steps

    def test_validation_fails_if_knowledge_check_below_threshold(self) -> None:
        # Arrange
        validation = CompetencyValidation(
            learner_id="learner-1",
            topic_id="topic-react-hooks",
            cohort_id="cohort-1",
        )

        # Act
        result = validation.validate(
            tasks_completed=True,
            knowledge_check_score=65,  # < 70% FAIL
            peer_review_received=True,
            mentor_approved=True,
        )

        # Assert
        assert result.is_valid is False
        assert ValidationStep.KNOWLEDGE_CHECK in result.failed_steps

    def test_validation_fails_if_no_peer_review(self) -> None:
        # Arrange
        validation = CompetencyValidation(
            learner_id="learner-1",
            topic_id="topic-react-hooks",
            cohort_id="cohort-1",
        )

        # Act
        result = validation.validate(
            tasks_completed=True,
            knowledge_check_score=80,
            peer_review_received=False,  # FAIL
            mentor_approved=True,
        )

        # Assert
        assert result.is_valid is False
        assert ValidationStep.PEER_REVIEW in result.failed_steps

    def test_validation_fails_if_mentor_not_approved(self) -> None:
        # Arrange
        validation = CompetencyValidation(
            learner_id="learner-1",
            topic_id="topic-react-hooks",
            cohort_id="cohort-1",
        )

        # Act
        result = validation.validate(
            tasks_completed=True,
            knowledge_check_score=80,
            peer_review_received=True,
            mentor_approved=False,  # FAIL
        )

        # Assert
        assert result.is_valid is False
        assert ValidationStep.MENTOR_APPROVAL in result.failed_steps

    def test_validation_can_fail_multiple_steps(self) -> None:
        # Arrange
        validation = CompetencyValidation(
            learner_id="learner-1",
            topic_id="topic-react-hooks",
            cohort_id="cohort-1",
        )

        # Act
        result = validation.validate(
            tasks_completed=False,  # FAIL
            knowledge_check_score=50,  # FAIL
            peer_review_received=False,  # FAIL
            mentor_approved=True,
        )

        # Assert
        assert result.is_valid is False
        assert len(result.failed_steps) == 3
        assert ValidationStep.TASK_COMPLETION in result.failed_steps
        assert ValidationStep.KNOWLEDGE_CHECK in result.failed_steps
        assert ValidationStep.PEER_REVIEW in result.failed_steps


class TestKnowledgeCheckThreshold:
    def test_default_threshold_is_70_percent(self) -> None:
        # Arrange
        validation = CompetencyValidation(
            learner_id="learner-1",
            topic_id="topic-react-hooks",
            cohort_id="cohort-1",
        )

        # Act
        result_pass = validation.validate(
            tasks_completed=True,
            knowledge_check_score=70,  # exactly 70%
            peer_review_received=True,
            mentor_approved=True,
        )
        result_fail = validation.validate(
            tasks_completed=True,
            knowledge_check_score=69,  # below 70%
            peer_review_received=True,
            mentor_approved=True,
        )

        # Assert
        assert result_pass.is_valid is True
        assert result_fail.is_valid is False

    def test_custom_threshold_can_be_set_per_topic(self) -> None:
        # Arrange
        validation = CompetencyValidation(
            learner_id="learner-1",
            topic_id="topic-advanced-react",
            cohort_id="cohort-1",
            knowledge_check_threshold=85,  # custom higher threshold
        )

        # Act
        result = validation.validate(
            tasks_completed=True,
            knowledge_check_score=80,  # would pass default 70%, fails 85%
            peer_review_received=True,
            mentor_approved=True,
        )

        # Assert
        assert result.is_valid is False
        assert ValidationStep.KNOWLEDGE_CHECK in result.failed_steps


class TestValidationResult:
    def test_validation_result_contains_failure_feedback(self) -> None:
        # Arrange
        validation = CompetencyValidation(
            learner_id="learner-1",
            topic_id="topic-react-hooks",
            cohort_id="cohort-1",
        )

        # Act
        result = validation.validate(
            tasks_completed=False,
            knowledge_check_score=65,
            peer_review_received=True,
            mentor_approved=True,
        )

        # Assert
        assert result.is_valid is False
        assert result.get_feedback() != ""
        assert "practice tasks" in result.get_feedback().lower()
        assert "knowledge check" in result.get_feedback().lower()
