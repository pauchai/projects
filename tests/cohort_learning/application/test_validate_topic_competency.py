"""Tests for ValidateTopicCompetency use case."""

import pytest

from cohort_learning.application.validate_topic_competency import (
    ValidateTopicCompetencyUseCase,
)
from cohort_learning.domain.competency_validation import ValidationStep
from tests.cohort_learning.fakes.fake_unit_of_work import FakeUnitOfWork
from tests.cohort_learning.factories import (
    make_active_cohort,
    make_active_task,
    save_cohort,
    save_task,
)


class TestValidateTopicCompetencyUseCase:
    """Validate Topic Competency for a learner in a cohort."""

    def test_successful_validation_when_all_steps_passed(self) -> None:
        """When all 4 validation steps pass, validation succeeds."""
        uow = FakeUnitOfWork()
        cohort = make_active_cohort()
        save_cohort(uow, cohort)

        # Create and submit task for topic t1
        task = make_active_task(topic_id="t1")
        task.add_submission(
            submission_id="sub1",
            learner_id="learner1",
            content="My solution",
        )
        save_task(uow, task)

        # Add a peer review for the submission
        from cohort_learning.domain.peer_review import PeerReview
        from cohort_learning.domain.review_score import ReviewScore

        review = PeerReview(
            review_id="rev1",
            submission_id="sub1",
            reviewer_id="learner2",
            task_id="task1",
            cohort_id="c1",
        )
        review.submit(
            scores=[ReviewScore(criterion="correctness", score=4)],
            overall_feedback="Good",
        )
        with uow:
            uow.peer_reviews.save(review)
            uow.commit()

        use_case = ValidateTopicCompetencyUseCase(uow=uow)

        result = use_case.execute(
            learner_id="learner1",
            topic_id="t1",
            cohort_id="c1",
            caller_id="master1",
            knowledge_check_score=80,
            mentor_approved=True,
        )

        assert result.is_valid is True
        assert len(result.failed_steps) == 0

    def test_validation_fails_when_no_tasks_submitted(self) -> None:
        """When learner has no submissions, task completion step fails."""
        uow = FakeUnitOfWork()
        cohort = make_active_cohort()
        save_cohort(uow, cohort)

        # Create task but no submissions
        task = make_active_task(topic_id="t1")
        save_task(uow, task)

        use_case = ValidateTopicCompetencyUseCase(uow=uow)

        result = use_case.execute(
            learner_id="learner1",
            topic_id="t1",
            cohort_id="c1",
            caller_id="master1",
            knowledge_check_score=80,
            mentor_approved=True,
        )

        assert result.is_valid is False
        assert ValidationStep.TASK_COMPLETION in result.failed_steps

    def test_validation_fails_when_knowledge_check_below_threshold(self) -> None:
        """When knowledge check score is below 70, validation fails."""
        uow = FakeUnitOfWork()
        cohort = make_active_cohort()
        save_cohort(uow, cohort)

        task = make_active_task(topic_id="t1")
        task.add_submission(
            submission_id="sub1",
            learner_id="learner1",
            content="My solution",
        )
        save_task(uow, task)

        use_case = ValidateTopicCompetencyUseCase(uow=uow)

        result = use_case.execute(
            learner_id="learner1",
            topic_id="t1",
            cohort_id="c1",
            caller_id="master1",
            knowledge_check_score=65,  # Below 70 threshold
            mentor_approved=True,
        )

        assert result.is_valid is False
        assert ValidationStep.KNOWLEDGE_CHECK in result.failed_steps

    def test_validation_fails_when_no_peer_review(self) -> None:
        """When no peer review received, validation fails."""
        uow = FakeUnitOfWork()
        cohort = make_active_cohort()
        save_cohort(uow, cohort)

        task = make_active_task(topic_id="t1")
        task.add_submission(
            submission_id="sub1",
            learner_id="learner1",
            content="My solution",
        )
        save_task(uow, task)

        use_case = ValidateTopicCompetencyUseCase(uow=uow)

        result = use_case.execute(
            learner_id="learner1",
            topic_id="t1",
            cohort_id="c1",
            caller_id="master1",
            knowledge_check_score=80,
            mentor_approved=True,
        )

        assert result.is_valid is False
        assert ValidationStep.PEER_REVIEW in result.failed_steps

    def test_validation_fails_when_mentor_not_approved(self) -> None:
        """When mentor doesn't approve, validation fails."""
        uow = FakeUnitOfWork()
        cohort = make_active_cohort()
        save_cohort(uow, cohort)

        task = make_active_task(topic_id="t1")
        task.add_submission(
            submission_id="sub1",
            learner_id="learner1",
            content="My solution",
        )
        save_task(uow, task)

        from cohort_learning.domain.peer_review import PeerReview
        from cohort_learning.domain.review_score import ReviewScore

        review = PeerReview(
            review_id="rev1",
            submission_id="sub1",
            reviewer_id="learner2",
            task_id="task1",
            cohort_id="c1",
        )
        review.submit(
            scores=[ReviewScore(criterion="correctness", score=4)],
            overall_feedback="Good",
        )
        with uow:
            uow.peer_reviews.save(review)
            uow.commit()

        use_case = ValidateTopicCompetencyUseCase(uow=uow)

        result = use_case.execute(
            learner_id="learner1",
            topic_id="t1",
            cohort_id="c1",
            caller_id="master1",
            knowledge_check_score=80,
            mentor_approved=False,
        )

        assert result.is_valid is False
        assert ValidationStep.MENTOR_APPROVAL in result.failed_steps

    def test_raises_when_caller_is_not_master_or_curator(self) -> None:
        """Only master or module curator can validate competency."""
        uow = FakeUnitOfWork()
        cohort = make_active_cohort()
        save_cohort(uow, cohort)

        use_case = ValidateTopicCompetencyUseCase(uow=uow)

        with pytest.raises(
            PermissionError,
            match="Only the cohort master or module curator",
        ):
            use_case.execute(
                learner_id="learner1",
                topic_id="t1",
                cohort_id="c1",
                caller_id="outsider",  # Not master or curator
                knowledge_check_score=80,
                mentor_approved=True,
            )

    def test_raises_when_cohort_not_found(self) -> None:
        """Validation fails if cohort doesn't exist."""
        uow = FakeUnitOfWork()
        use_case = ValidateTopicCompetencyUseCase(uow=uow)

        with pytest.raises(LookupError, match="Cohort.*not found"):
            use_case.execute(
                learner_id="learner1",
                topic_id="t1",
                cohort_id="nonexistent",
                caller_id="master1",
                knowledge_check_score=80,
                mentor_approved=True,
            )

    def test_commits_transaction(self) -> None:
        """Use case commits the transaction after validation."""
        uow = FakeUnitOfWork()
        cohort = make_active_cohort()
        save_cohort(uow, cohort)

        task = make_active_task(topic_id="t1")
        task.add_submission(
            submission_id="sub1",
            learner_id="learner1",
            content="My solution",
        )
        save_task(uow, task)

        from cohort_learning.domain.peer_review import PeerReview
        from cohort_learning.domain.review_score import ReviewScore

        review = PeerReview(
            review_id="rev1",
            submission_id="sub1",
            reviewer_id="learner2",
            task_id="task1",
            cohort_id="c1",
        )
        review.submit(
            scores=[ReviewScore(criterion="correctness", score=4)],
            overall_feedback="Good",
        )
        with uow:
            uow.peer_reviews.save(review)
            uow.commit()

        use_case = ValidateTopicCompetencyUseCase(uow=uow)

        use_case.execute(
            learner_id="learner1",
            topic_id="t1",
            cohort_id="c1",
            caller_id="master1",
            knowledge_check_score=80,
            mentor_approved=True,
        )

        assert uow.committed is True
