"""Tests for cohort_learning domain ports — repositories and UnitOfWork."""

import pytest

from cohort_learning.domain.events import (
    CohortFormed,
    PracticeTaskCreated,
    PeerReviewSubmitted,
)
from cohort_learning.domain.learning_cohort import LearningCohort
from cohort_learning.domain.peer_review import PeerReview
from cohort_learning.domain.practice_task import PracticeTask
from cohort_learning.domain.review_score import ReviewScore
from tests.cohort_learning.factories import make_cohort, make_task, make_review
from tests.cohort_learning.fakes.fake_unit_of_work import FakeUnitOfWork


class TestFakeCohortRepository:
    """Verify the fake repository satisfies the CohortRepository protocol."""

    def test_save_and_find_by_id(self) -> None:
        uow = FakeUnitOfWork()
        cohort = make_cohort(cohort_id="c1")
        with uow:
            uow.cohorts.save(cohort)
            uow.commit()
        found = uow.cohorts.find_by_id("c1")
        assert found is not None
        assert found.cohort_id == "c1"

    def test_find_by_id_returns_none_for_missing(self) -> None:
        uow = FakeUnitOfWork()
        assert uow.cohorts.find_by_id("nonexistent") is None

    def test_save_collects_events(self) -> None:
        uow = FakeUnitOfWork()
        cohort = make_cohort(cohort_id="c1")
        with uow:
            uow.cohorts.save(cohort)
            # Events should have been collected from the aggregate
            assert len(uow._pending_events) >= 1
            uow.commit()


class TestFakeUnitOfWork:
    """Verify commit/rollback semantics of the fake UoW."""

    def test_commit_keeps_changes(self) -> None:
        uow = FakeUnitOfWork()
        cohort = make_cohort(cohort_id="c1")
        with uow:
            uow.cohorts.save(cohort)
            uow.commit()
        assert uow.cohorts.find_by_id("c1") is not None

    def test_rollback_discards_changes(self) -> None:
        uow = FakeUnitOfWork()
        cohort = make_cohort(cohort_id="c1")
        with uow:
            uow.cohorts.save(cohort)
            uow.rollback()
        assert uow.cohorts.find_by_id("c1") is None

    def test_exit_without_commit_rolls_back(self) -> None:
        uow = FakeUnitOfWork()
        cohort = make_cohort(cohort_id="c1")
        with uow:
            uow.cohorts.save(cohort)
            # no commit — should rollback on exit
        assert uow.cohorts.find_by_id("c1") is None

    def test_committed_flag(self) -> None:
        uow = FakeUnitOfWork()
        assert uow.committed is False
        with uow:
            uow.cohorts.save(make_cohort())
            uow.commit()
        assert uow.committed is True


class TestFakePracticeTaskRepository:
    """Verify the fake repository satisfies the PracticeTaskRepository protocol."""

    def test_save_and_find_by_id(self) -> None:
        uow = FakeUnitOfWork()
        task = make_task(task_id="task1")
        with uow:
            uow.practice_tasks.save(task)
            uow.commit()
        found = uow.practice_tasks.find_by_id("task1")
        assert found is not None
        assert found.task_id == "task1"

    def test_find_by_id_returns_none_for_missing(self) -> None:
        uow = FakeUnitOfWork()
        assert uow.practice_tasks.find_by_id("nonexistent") is None

    def test_find_by_cohort(self) -> None:
        uow = FakeUnitOfWork()
        task1 = make_task(task_id="task1", cohort_id="c1")
        task2 = make_task(task_id="task2", cohort_id="c1")
        task3 = make_task(task_id="task3", cohort_id="c2")
        with uow:
            uow.practice_tasks.save(task1)
            uow.practice_tasks.save(task2)
            uow.practice_tasks.save(task3)
            uow.commit()
        results = uow.practice_tasks.find_by_cohort("c1")
        assert len(results) == 2
        assert all(t.cohort_id == "c1" for t in results)

    def test_save_collects_events(self) -> None:
        uow = FakeUnitOfWork()
        task = make_task(task_id="task1")
        with uow:
            uow.practice_tasks.save(task)
            assert len(uow._pending_events) >= 1
            uow.commit()


class TestFakePeerReviewRepository:
    """Verify the fake repository satisfies the PeerReviewRepository protocol."""

    def test_save_and_find_by_id(self) -> None:
        uow = FakeUnitOfWork()
        review = make_review(review_id="rev1")
        with uow:
            uow.peer_reviews.save(review)
            uow.commit()
        found = uow.peer_reviews.find_by_id("rev1")
        assert found is not None
        assert found.review_id == "rev1"

    def test_find_by_id_returns_none_for_missing(self) -> None:
        uow = FakeUnitOfWork()
        assert uow.peer_reviews.find_by_id("nonexistent") is None

    def test_find_by_submission(self) -> None:
        uow = FakeUnitOfWork()
        rev1 = make_review(review_id="rev1", submission_id="sub1")
        rev2 = make_review(
            review_id="rev2", submission_id="sub1", reviewer_id="learner3"
        )
        rev3 = make_review(review_id="rev3", submission_id="sub2")
        with uow:
            uow.peer_reviews.save(rev1)
            uow.peer_reviews.save(rev2)
            uow.peer_reviews.save(rev3)
            uow.commit()
        results = uow.peer_reviews.find_by_submission("sub1")
        assert len(results) == 2
        assert all(r.submission_id == "sub1" for r in results)

    def test_save_collects_events_on_submitted_review(self) -> None:
        uow = FakeUnitOfWork()
        review = make_review(review_id="rev1")
        scores = [ReviewScore(criterion="clarity", score=4)]
        review.submit(scores=scores, overall_feedback="Good")
        with uow:
            uow.peer_reviews.save(review)
            assert any(isinstance(e, PeerReviewSubmitted) for e in uow._pending_events)
            uow.commit()


class TestFakeUnitOfWorkWithNewRepos:
    """Verify that UoW correctly handles rollback for all repositories."""

    def test_rollback_discards_task_changes(self) -> None:
        uow = FakeUnitOfWork()
        task = make_task(task_id="task1")
        with uow:
            uow.practice_tasks.save(task)
            uow.rollback()
        assert uow.practice_tasks.find_by_id("task1") is None

    def test_rollback_discards_review_changes(self) -> None:
        uow = FakeUnitOfWork()
        review = make_review(review_id="rev1")
        with uow:
            uow.peer_reviews.save(review)
            uow.rollback()
        assert uow.peer_reviews.find_by_id("rev1") is None

    def test_exit_without_commit_rolls_back_all_repos(self) -> None:
        uow = FakeUnitOfWork()
        task = make_task(task_id="task1")
        review = make_review(review_id="rev1")
        with uow:
            uow.practice_tasks.save(task)
            uow.peer_reviews.save(review)
            # no commit
        assert uow.practice_tasks.find_by_id("task1") is None
        assert uow.peer_reviews.find_by_id("rev1") is None
