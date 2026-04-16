"""Competency Validation domain service — validates topic mastery."""

from dataclasses import dataclass
from enum import Enum


# Default minimum passing score for knowledge check (per glossary)
DEFAULT_KNOWLEDGE_CHECK_THRESHOLD = 70


class ValidationStep(Enum):
    """
    The four required steps for Topic Competency validation (per glossary).
    """

    TASK_COMPLETION = "task_completion"
    KNOWLEDGE_CHECK = "knowledge_check"
    PEER_REVIEW = "peer_review"
    MENTOR_APPROVAL = "mentor_approval"


@dataclass(frozen=True)
class ValidationResult:
    """
    Result of competency validation attempt.

    Attributes:
        is_valid: True if all validation steps passed
        failed_steps: List of validation steps that failed
    """

    is_valid: bool
    failed_steps: list[ValidationStep]

    def get_feedback(self) -> str:
        """Generate human-readable feedback for failed validation."""
        if self.is_valid:
            return "All validation steps passed successfully."

        feedback_lines = ["Validation failed. Please address the following:"]

        for step in self.failed_steps:
            if step == ValidationStep.TASK_COMPLETION:
                feedback_lines.append(
                    "- Complete all required practice tasks for this topic"
                )
            elif step == ValidationStep.KNOWLEDGE_CHECK:
                feedback_lines.append(
                    "- Pass the knowledge check with minimum required score"
                )
            elif step == ValidationStep.PEER_REVIEW:
                feedback_lines.append(
                    "- Receive at least one peer review on your task submissions"
                )
            elif step == ValidationStep.MENTOR_APPROVAL:
                feedback_lines.append("- Obtain mentor approval for topic competency")

        return "\n".join(feedback_lines)


class CompetencyValidation:
    """
    Domain service for validating Topic Competency.

    Per glossary, validation requires four steps:
    1. Task Completion — all required practice tasks submitted and approved
    2. Knowledge Check — automated quiz with minimum passing score
    3. Peer Review — at least one task reviewed positively by a peer
    4. Mentor Approval — Master or Module Curator confirms readiness

    All four steps must pass for Topic Competency to be achieved.
    """

    def __init__(
        self,
        learner_id: str,
        topic_id: str,
        cohort_id: str,
        knowledge_check_threshold: int = DEFAULT_KNOWLEDGE_CHECK_THRESHOLD,
    ) -> None:
        self.learner_id = learner_id
        self.topic_id = topic_id
        self.cohort_id = cohort_id
        self.knowledge_check_threshold = knowledge_check_threshold

    def validate(
        self,
        tasks_completed: bool,
        knowledge_check_score: int,
        peer_review_received: bool,
        mentor_approved: bool,
    ) -> ValidationResult:
        """
        Validate Topic Competency based on completion of all four steps.

        Args:
            tasks_completed: All required tasks for the topic are submitted
            knowledge_check_score: Score (0-100) on knowledge check quiz
            peer_review_received: At least one peer review received
            mentor_approved: Master or Module Curator approved

        Returns:
            ValidationResult with overall validity and list of failed steps
        """
        failed_steps: list[ValidationStep] = []

        # Step 1: Task Completion
        if not tasks_completed:
            failed_steps.append(ValidationStep.TASK_COMPLETION)

        # Step 2: Knowledge Check
        if knowledge_check_score < self.knowledge_check_threshold:
            failed_steps.append(ValidationStep.KNOWLEDGE_CHECK)

        # Step 3: Peer Review
        if not peer_review_received:
            failed_steps.append(ValidationStep.PEER_REVIEW)

        # Step 4: Mentor Approval
        if not mentor_approved:
            failed_steps.append(ValidationStep.MENTOR_APPROVAL)

        is_valid = len(failed_steps) == 0

        return ValidationResult(is_valid=is_valid, failed_steps=failed_steps)
