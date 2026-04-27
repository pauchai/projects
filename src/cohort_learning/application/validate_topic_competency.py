"""ValidateTopicCompetency use case."""

from cohort_learning.application._helpers import (
    get_cohort_or_raise,
    require_master_or_curator,
)
from cohort_learning.domain.competency_validation import (
    CompetencyValidation,
    ValidationResult,
)
from cohort_learning.domain.ports import UnitOfWork


class ValidateTopicCompetencyUseCase:
    """Validate Topic Competency for a learner in a specific topic.

    Validates that a learner has:
    1. Completed all required practice tasks for the topic
    2. Passed knowledge check with minimum score (default 70%)
    3. Received at least one peer review on their submissions
    4. Received mentor approval (Master or Module Curator)

    Only Master or Module Curator can perform this validation.
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(
        self,
        learner_id: str,
        topic_id: str,
        cohort_id: str,
        caller_id: str,
        knowledge_check_score: int,
        mentor_approved: bool,
    ) -> ValidationResult:
        with self._uow as uow:
            cohort = get_cohort_or_raise(uow, cohort_id)
            require_master_or_curator(cohort, caller_id)

            # Gather validation data from repositories

            # Step 1: Check task completion
            tasks_completed = self._check_tasks_completed(
                uow, learner_id, topic_id, cohort_id
            )

            # Step 3: Check peer review received
            peer_review_received = self._check_peer_review_received(
                uow, learner_id, topic_id, cohort_id
            )

            # Step 2 & 4: knowledge_check_score and mentor_approved are provided

            # Validate using domain service
            validation_service = CompetencyValidation(
                learner_id=learner_id,
                topic_id=topic_id,
                cohort_id=cohort_id,
            )

            result = validation_service.validate(
                tasks_completed=tasks_completed,
                knowledge_check_score=knowledge_check_score,
                peer_review_received=peer_review_received,
                mentor_approved=mentor_approved,
            )

            uow.commit()
            return result

    def _check_tasks_completed(
        self, uow: UnitOfWork, learner_id: str, topic_id: str, cohort_id: str
    ) -> bool:
        """Check if learner has submitted all required tasks for the topic."""
        tasks = uow.practice_tasks.find_by_cohort(cohort_id)
        topic_tasks = [t for t in tasks if t.topic_id == topic_id]

        if not topic_tasks:
            return False  # No tasks for this topic means no completion

        # Check if learner has at least one submission for this topic
        for task in topic_tasks:
            submissions = [s for s in task.submissions if s.learner_id == learner_id]
            if submissions:
                return True

        return False

    def _check_peer_review_received(
        self, uow: UnitOfWork, learner_id: str, topic_id: str, cohort_id: str
    ) -> bool:
        """Check if learner has received at least one peer review for the topic."""
        tasks = uow.practice_tasks.find_by_cohort(cohort_id)
        topic_tasks = [t for t in tasks if t.topic_id == topic_id]

        for task in topic_tasks:
            # Find submissions by this learner
            learner_submissions = [
                s for s in task.submissions if s.learner_id == learner_id
            ]

            # Check if any submission has a review
            for submission in learner_submissions:
                reviews = uow.peer_reviews.find_by_submission(submission.submission_id)
                if reviews:
                    return True

        return False
