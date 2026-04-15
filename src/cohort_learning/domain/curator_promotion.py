"""Curator Promotion domain service — validates Module Curator eligibility."""

from dataclasses import dataclass
from enum import Enum

from cohort_learning.domain.helper_metrics import HelperMetrics


class PromotionRequirement(Enum):
    """
    The four required criteria for Module Curator promotion (per glossary).
    """

    MODULE_COMPLETION = "module_completion"
    HELPER_TRACK_RECORD = "helper_track_record"
    TEACHING_TRIAL = "teaching_trial"
    MASTER_APPROVAL = "master_approval"


@dataclass(frozen=True)
class PromotionResult:
    """
    Result of curator promotion evaluation.

    Attributes:
        is_approved: True if all promotion requirements met
        failed_requirements: List of requirements that were not satisfied
    """

    is_approved: bool
    failed_requirements: list[PromotionRequirement]

    def get_feedback(self) -> str:
        """Generate human-readable feedback for failed promotion."""
        if self.is_approved:
            return "All promotion requirements met. Ready for Module Curator status."

        feedback_lines = ["Curator promotion not yet available. Requirements:"]

        for requirement in self.failed_requirements:
            if requirement == PromotionRequirement.MODULE_COMPLETION:
                feedback_lines.append(
                    "- Complete the entire Module Progression and achieve Topic Competency in all topics"
                )
            elif requirement == PromotionRequirement.HELPER_TRACK_RECORD:
                feedback_lines.append(
                    "- Build Helper track record: help ≥3 learners, review ≥5 tasks, maintain ≥4.0 satisfaction"
                )
            elif requirement == PromotionRequirement.TEACHING_TRIAL:
                feedback_lines.append(
                    "- Successfully complete teaching trial (assist 2-3 learners through at least one topic)"
                )
            elif requirement == PromotionRequirement.MASTER_APPROVAL:
                feedback_lines.append(
                    "- Obtain Master's explicit approval for promotion"
                )

        return "\n".join(feedback_lines)


class CuratorPromotionService:
    """
    Domain service for evaluating Module Curator promotion eligibility.

    Per glossary, promotion requires four criteria:
    1. Module Completion — completed entire Module Progression with Topic Competency in all topics
    2. Peer Helper Track Record — Helper Metrics meet minimum threshold (≥3 learners, ≥4.0 satisfaction)
    3. Teaching Trial — successfully assisted 2-3 learners under Master supervision
    4. Master Approval — Master explicitly approves based on overall assessment

    All four criteria must be met for promotion to be granted.
    """

    def evaluate_promotion(
        self,
        learner_id: str,
        module_id: str,
        helper_metrics: HelperMetrics,
        module_completed: bool,
        teaching_trial_passed: bool,
        master_approved: bool,
    ) -> PromotionResult:
        """
        Evaluate Module Curator promotion eligibility.

        Args:
            learner_id: Learner requesting promotion
            module_id: Module for which curator status is requested
            helper_metrics: Aggregated peer helping activity metrics
            module_completed: All topics completed with Topic Competency
            teaching_trial_passed: Teaching trial evaluation passed
            master_approved: Master has explicitly approved promotion

        Returns:
            PromotionResult with overall approval and list of failed requirements
        """
        failed_requirements: list[PromotionRequirement] = []

        # Requirement 1: Module Completion
        if not module_completed:
            failed_requirements.append(PromotionRequirement.MODULE_COMPLETION)

        # Requirement 2: Helper Track Record
        # Delegate to HelperMetrics.meets_curator_threshold() for threshold check
        if not helper_metrics.meets_curator_threshold():
            failed_requirements.append(PromotionRequirement.HELPER_TRACK_RECORD)

        # Requirement 3: Teaching Trial
        if not teaching_trial_passed:
            failed_requirements.append(PromotionRequirement.TEACHING_TRIAL)

        # Requirement 4: Master Approval
        if not master_approved:
            failed_requirements.append(PromotionRequirement.MASTER_APPROVAL)

        is_approved = len(failed_requirements) == 0

        return PromotionResult(
            is_approved=is_approved, failed_requirements=failed_requirements
        )
