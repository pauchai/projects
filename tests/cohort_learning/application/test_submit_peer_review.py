"""Tests for SubmitPeerReview use case."""

import pytest

from cohort_learning.application.submit_peer_review import SubmitPeerReviewUseCase
from cohort_learning.domain.events import PeerReviewSubmitted
from cohort_learning.domain.review_score import ReviewScore
from cohort_learning.domain.review_status import ReviewStatus
from shared_kernel.events import DomainEvent
from tests.cohort_learning.fakes.fake_unit_of_work import FakeUnitOfWork
from tests.cohort_learning.factories import (
    make_active_cohort,
    make_active_task,
    save_cohort,
    save_task,
)


class _SpyEventBus:
    def __init__(self) -> None:
        self.published: list[DomainEvent] = []

    def publish(self, events: list[DomainEvent]) -> None:
        self.published.extend(events)


def _setup_with_submission(
    uow: FakeUnitOfWork,
    submitter_id: str = "learner1",
) -> None:
    """Create active cohort, active task, and a submission by submitter_id."""
    cohort = make_active_cohort()
    save_cohort(uow, cohort)
    task = make_active_task()
    task.add_submission(
        submission_id="sub1",
        learner_id=submitter_id,
        content="My solution",
    )
    task.collect_events()  # Clear domain events from setup
    save_task(uow, task)


class TestSubmitPeerReviewUseCase:
    """A cohort member reviews another member's submission."""

    def test_creates_submitted_review(self) -> None:
        uow = FakeUnitOfWork()
        _setup_with_submission(uow)
        use_case = SubmitPeerReviewUseCase(uow=uow)

        result = use_case.execute(
            review_id="rev1",
            submission_id="sub1",
            task_id="task1",
            reviewer_id="learner2",
            scores=[ReviewScore(criterion="correctness", score=4)],
            overall_feedback="Good work",
        )

        assert result.review_id == "rev1"
        assert result.status == ReviewStatus.SUBMITTED
        assert result.overall_feedback == "Good work"
        assert len(result.scores) == 1
        assert result.scores[0].criterion == "correctness"

    def test_persists_review_in_repository(self) -> None:
        uow = FakeUnitOfWork()
        _setup_with_submission(uow)
        use_case = SubmitPeerReviewUseCase(uow=uow)

        use_case.execute(
            review_id="rev1",
            submission_id="sub1",
            task_id="task1",
            reviewer_id="learner2",
            scores=[ReviewScore(criterion="correctness", score=4)],
        )

        saved = uow.peer_reviews.find_by_id("rev1")
        assert saved is not None
        assert saved.submission_id == "sub1"

    def test_commits_transaction(self) -> None:
        uow = FakeUnitOfWork()
        _setup_with_submission(uow)
        use_case = SubmitPeerReviewUseCase(uow=uow)

        use_case.execute(
            review_id="rev1",
            submission_id="sub1",
            task_id="task1",
            reviewer_id="learner2",
            scores=[ReviewScore(criterion="correctness", score=4)],
        )

        assert uow.committed is True

    def test_emits_peer_review_submitted_event(self) -> None:
        spy_bus = _SpyEventBus()
        uow = FakeUnitOfWork(event_bus=spy_bus)
        _setup_with_submission(uow)
        use_case = SubmitPeerReviewUseCase(uow=uow)

        use_case.execute(
            review_id="rev1",
            submission_id="sub1",
            task_id="task1",
            reviewer_id="learner2",
            scores=[ReviewScore(criterion="correctness", score=4)],
        )

        review_events = [
            e for e in spy_bus.published if isinstance(e, PeerReviewSubmitted)
        ]
        assert len(review_events) == 1
        assert review_events[0].review_id == "rev1"
        assert review_events[0].reviewer_id == "learner2"

    def test_raises_when_task_not_found(self) -> None:
        uow = FakeUnitOfWork()
        use_case = SubmitPeerReviewUseCase(uow=uow)

        with pytest.raises(LookupError, match="Task.*not found"):
            use_case.execute(
                review_id="rev1",
                submission_id="sub1",
                task_id="nonexistent",
                reviewer_id="learner2",
                scores=[ReviewScore(criterion="correctness", score=4)],
            )

    def test_raises_when_submission_not_found(self) -> None:
        uow = FakeUnitOfWork()
        _setup_with_submission(uow)
        use_case = SubmitPeerReviewUseCase(uow=uow)

        with pytest.raises(LookupError, match="Submission.*not found"):
            use_case.execute(
                review_id="rev1",
                submission_id="nonexistent",
                task_id="task1",
                reviewer_id="learner2",
                scores=[ReviewScore(criterion="correctness", score=4)],
            )

    def test_raises_when_reviewer_is_not_cohort_member(self) -> None:
        uow = FakeUnitOfWork()
        _setup_with_submission(uow)
        use_case = SubmitPeerReviewUseCase(uow=uow)

        with pytest.raises(PermissionError, match="not an active member"):
            use_case.execute(
                review_id="rev1",
                submission_id="sub1",
                task_id="task1",
                reviewer_id="outsider",
                scores=[ReviewScore(criterion="correctness", score=4)],
            )

    def test_raises_when_reviewer_is_submission_author(self) -> None:
        uow = FakeUnitOfWork()
        _setup_with_submission(uow, submitter_id="learner1")
        use_case = SubmitPeerReviewUseCase(uow=uow)

        with pytest.raises(PermissionError, match="own submission"):
            use_case.execute(
                review_id="rev1",
                submission_id="sub1",
                task_id="task1",
                reviewer_id="learner1",
                scores=[ReviewScore(criterion="correctness", score=4)],
            )

    def test_review_with_multiple_scores(self) -> None:
        uow = FakeUnitOfWork()
        _setup_with_submission(uow)
        use_case = SubmitPeerReviewUseCase(uow=uow)

        result = use_case.execute(
            review_id="rev1",
            submission_id="sub1",
            task_id="task1",
            reviewer_id="learner2",
            scores=[
                ReviewScore(criterion="correctness", score=5),
                ReviewScore(criterion="readability", score=3),
                ReviewScore(criterion="efficiency", score=4),
            ],
            overall_feedback="Solid work overall",
        )

        assert len(result.scores) == 3
        assert result.average_score == pytest.approx(4.0)
