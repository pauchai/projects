"""Integration tests for SqlAlchemyPracticeTaskRepository, SqlAlchemyPeerReviewRepository,
and SqlAlchemyUnitOfWork with the new peer review system repositories.

These tests verify the real PostgreSQL persistence layer:
- Round-trip save/load of PracticeTask aggregates (with submissions)
- Round-trip save/load of PeerReview aggregates (with ReviewScore conversion)
- Persistence of enum columns (TaskStatus, SubmissionStatus, ReviewStatus)
- Upsert semantics (save twice updates)
- find_by_cohort and find_by_submission queries
- UoW with practice_tasks and peer_reviews repos
- Domain event publishing through extended UoW

Requires ``docker compose up -d postgres-test`` (port 5433).
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy.orm import Session, sessionmaker

from cohort_learning.domain.learning_cohort import LearningCohort
from cohort_learning.domain.peer_review import PeerReview
from cohort_learning.domain.practice_task import PracticeTask
from cohort_learning.domain.review_score import ReviewScore
from cohort_learning.domain.review_status import ReviewStatus
from cohort_learning.domain.task_status import SubmissionStatus, TaskStatus
from cohort_learning.infrastructure.sqlalchemy_repository import (
    SqlAlchemyPeerReviewRepository,
    SqlAlchemyPracticeTaskRepository,
)
from cohort_learning.infrastructure.sqlalchemy_unit_of_work import (
    SqlAlchemyUnitOfWork,
)
from shared_kernel.events import DomainEvent
from shared_kernel.in_process_event_bus import InProcessEventBus

from cohort_learning.domain.events import (
    PracticeTaskCreated,
    PeerReviewSubmitted,
    TaskSubmissionCreated,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_task(**overrides: object) -> PracticeTask:
    """Create a PracticeTask with defaults and clear creation events."""
    defaults: dict = dict(
        task_id="t1",
        cohort_id="c1",
        topic_id="topic1",
        creator_id="creator1",
        title="Test Task",
        description="A test practice task",
    )
    defaults.update(overrides)
    task = PracticeTask(**defaults)
    task.collect_events()  # clear creation events
    return task


def _make_active_task(**overrides: object) -> PracticeTask:
    """Create an active PracticeTask (Draft → Active)."""
    task = _make_task(**overrides)
    task.activate()
    return task


def _make_review(**overrides: object) -> PeerReview:
    """Create a PeerReview with defaults."""
    defaults: dict = dict(
        review_id="r1",
        submission_id="s1",
        reviewer_id="reviewer1",
        task_id="t1",
        cohort_id="c1",
    )
    defaults.update(overrides)
    return PeerReview(**defaults)


def _make_cohort_for_task() -> LearningCohort:
    """Create a cohort suitable for practice task tests."""
    cohort = LearningCohort(cohort_id="c1", master_id="master1", module_id="mod1")
    cohort.collect_events()
    return cohort


# ---------------------------------------------------------------------------
# PracticeTask Repository: find_by_id
# ---------------------------------------------------------------------------


class TestPracticeTaskFindById:
    """Tests for SqlAlchemyPracticeTaskRepository.find_by_id."""

    def test_returns_none_for_nonexistent_task(
        self, integration_session: Session
    ) -> None:
        repo = SqlAlchemyPracticeTaskRepository(integration_session)

        result = repo.find_by_id("nonexistent")

        assert result is None

    def test_round_trip_saves_and_loads_task(
        self, integration_session: Session
    ) -> None:
        repo = SqlAlchemyPracticeTaskRepository(integration_session)
        task = _make_task()

        repo.save(task)
        loaded = repo.find_by_id("t1")

        assert loaded is not None
        assert loaded.task_id == "t1"
        assert loaded.cohort_id == "c1"
        assert loaded.topic_id == "topic1"
        assert loaded.creator_id == "creator1"
        assert loaded.title == "Test Task"
        assert loaded.description == "A test practice task"
        assert loaded.status == TaskStatus.DRAFT
        assert loaded.created_at is not None

    def test_persists_active_status(self, integration_session: Session) -> None:
        repo = SqlAlchemyPracticeTaskRepository(integration_session)
        task = _make_active_task()

        repo.save(task)
        loaded = repo.find_by_id("t1")

        assert loaded is not None
        assert loaded.status == TaskStatus.ACTIVE

    def test_persists_closed_status(self, integration_session: Session) -> None:
        repo = SqlAlchemyPracticeTaskRepository(integration_session)
        task = _make_task()
        task.close()

        repo.save(task)
        loaded = repo.find_by_id("t1")

        assert loaded is not None
        assert loaded.status == TaskStatus.CLOSED


# ---------------------------------------------------------------------------
# PracticeTask Repository: submission persistence
# ---------------------------------------------------------------------------


class TestPracticeTaskSubmissionPersistence:
    """Tests for persistence of TaskSubmission entities within PracticeTask."""

    def test_persists_submissions(self, integration_session: Session) -> None:
        repo = SqlAlchemyPracticeTaskRepository(integration_session)
        task = _make_active_task()
        task.add_submission(
            submission_id="s1", learner_id="learner1", content="My solution"
        )
        task.collect_events()

        repo.save(task)
        loaded = repo.find_by_id("t1")

        assert loaded is not None
        assert len(loaded.submissions) == 1
        sub = loaded.submissions[0]
        assert sub.submission_id == "s1"
        assert sub.learner_id == "learner1"
        assert sub.content == "My solution"
        assert sub.status == SubmissionStatus.SUBMITTED

    def test_persists_multiple_submissions(self, integration_session: Session) -> None:
        repo = SqlAlchemyPracticeTaskRepository(integration_session)
        task = _make_active_task()
        task.add_submission(
            submission_id="s1", learner_id="learner1", content="Solution 1"
        )
        task.add_submission(
            submission_id="s2", learner_id="learner2", content="Solution 2"
        )
        task.collect_events()

        repo.save(task)
        loaded = repo.find_by_id("t1")

        assert loaded is not None
        assert len(loaded.submissions) == 2
        learner_ids = {s.learner_id for s in loaded.submissions}
        assert learner_ids == {"learner1", "learner2"}

    def test_persists_submission_status_change(
        self, integration_session: Session
    ) -> None:
        repo = SqlAlchemyPracticeTaskRepository(integration_session)
        task = _make_active_task()
        sub = task.add_submission(
            submission_id="s1", learner_id="learner1", content="My solution"
        )
        sub.begin_review()
        task.collect_events()

        repo.save(task)
        loaded = repo.find_by_id("t1")

        assert loaded is not None
        loaded_sub = loaded.submissions[0]
        assert loaded_sub.status == SubmissionStatus.IN_REVIEW

    def test_persists_submission_submitted_at(
        self, integration_session: Session
    ) -> None:
        repo = SqlAlchemyPracticeTaskRepository(integration_session)
        task = _make_active_task()
        sub = task.add_submission(
            submission_id="s1", learner_id="learner1", content="My solution"
        )
        original_submitted = sub.submitted_at
        task.collect_events()

        repo.save(task)
        loaded = repo.find_by_id("t1")

        assert loaded is not None
        loaded_sub = loaded.submissions[0]
        assert loaded_sub.submitted_at is not None
        assert loaded_sub.submitted_at.replace(
            microsecond=0
        ) == original_submitted.replace(microsecond=0)


# ---------------------------------------------------------------------------
# PracticeTask Repository: find_by_cohort
# ---------------------------------------------------------------------------


class TestPracticeTaskFindByCohort:
    """Tests for SqlAlchemyPracticeTaskRepository.find_by_cohort."""

    def test_returns_empty_list_when_no_tasks(
        self, integration_session: Session
    ) -> None:
        repo = SqlAlchemyPracticeTaskRepository(integration_session)

        result = repo.find_by_cohort("nonexistent")

        assert result == []

    def test_returns_tasks_for_cohort(self, integration_session: Session) -> None:
        repo = SqlAlchemyPracticeTaskRepository(integration_session)
        task1 = _make_task(task_id="t1", cohort_id="c1", title="Task 1")
        task2 = _make_task(task_id="t2", cohort_id="c1", title="Task 2")
        task_other = _make_task(task_id="t3", cohort_id="c2", title="Other")

        repo.save(task1)
        repo.save(task2)
        repo.save(task_other)

        result = repo.find_by_cohort("c1")

        assert len(result) == 2
        task_ids = {t.task_id for t in result}
        assert task_ids == {"t1", "t2"}

    def test_find_by_cohort_loads_submissions(
        self, integration_session: Session
    ) -> None:
        repo = SqlAlchemyPracticeTaskRepository(integration_session)
        task = _make_active_task()
        task.add_submission(
            submission_id="s1", learner_id="learner1", content="My solution"
        )
        task.collect_events()

        repo.save(task)
        result = repo.find_by_cohort("c1")

        assert len(result) == 1
        assert len(result[0].submissions) == 1


# ---------------------------------------------------------------------------
# PracticeTask Repository: upsert
# ---------------------------------------------------------------------------


class TestPracticeTaskUpsert:
    """Verify that save() is idempotent (upsert semantics)."""

    def test_save_twice_updates_existing_task(
        self, integration_session: Session
    ) -> None:
        repo = SqlAlchemyPracticeTaskRepository(integration_session)
        task = _make_task()

        repo.save(task)

        task.activate()
        task.collect_events()
        repo.save(task)

        loaded = repo.find_by_id("t1")
        assert loaded is not None
        assert loaded.status == TaskStatus.ACTIVE


# ---------------------------------------------------------------------------
# PracticeTask Repository: reconstitution
# ---------------------------------------------------------------------------


class TestPracticeTaskReconstitution:
    """Verify reconstituted tasks have clean transient state."""

    def test_reconstituted_task_has_empty_events(
        self, integration_session: Session
    ) -> None:
        repo = SqlAlchemyPracticeTaskRepository(integration_session)
        task = _make_task()

        repo.save(task)
        loaded = repo.find_by_id("t1")

        assert loaded is not None
        assert loaded._events == []


# ---------------------------------------------------------------------------
# PeerReview Repository: find_by_id
# ---------------------------------------------------------------------------


class TestPeerReviewFindById:
    """Tests for SqlAlchemyPeerReviewRepository.find_by_id."""

    def test_returns_none_for_nonexistent_review(
        self, integration_session: Session
    ) -> None:
        repo = SqlAlchemyPeerReviewRepository(integration_session)

        result = repo.find_by_id("nonexistent")

        assert result is None

    def test_round_trip_saves_and_loads_draft_review(
        self, integration_session: Session
    ) -> None:
        repo = SqlAlchemyPeerReviewRepository(integration_session)
        review = _make_review()

        repo.save(review)
        loaded = repo.find_by_id("r1")

        assert loaded is not None
        assert loaded.review_id == "r1"
        assert loaded.submission_id == "s1"
        assert loaded.reviewer_id == "reviewer1"
        assert loaded.task_id == "t1"
        assert loaded.cohort_id == "c1"
        assert loaded.status == ReviewStatus.DRAFT
        assert loaded.overall_feedback == ""
        assert loaded.scores == []
        assert loaded.created_at is not None
        assert loaded.reviewed_at is None


# ---------------------------------------------------------------------------
# PeerReview Repository: score persistence (ReviewScore ↔ ReviewScoreRecord)
# ---------------------------------------------------------------------------


class TestPeerReviewScorePersistence:
    """Tests for ReviewScore value object round-trip through ReviewScoreRecord."""

    def test_persists_scores_after_submit(self, integration_session: Session) -> None:
        repo = SqlAlchemyPeerReviewRepository(integration_session)
        review = _make_review()
        review.submit(
            scores=[
                ReviewScore(criterion="clarity", score=4, comment="Good"),
                ReviewScore(criterion="correctness", score=5, comment="Excellent"),
            ],
            overall_feedback="Well done",
        )
        review.collect_events()

        repo.save(review)
        loaded = repo.find_by_id("r1")

        assert loaded is not None
        assert loaded.status == ReviewStatus.SUBMITTED
        assert loaded.overall_feedback == "Well done"
        assert loaded.reviewed_at is not None
        assert len(loaded.scores) == 2

        # Verify domain ReviewScore value objects are reconstituted correctly
        criteria = {s.criterion for s in loaded.scores}
        assert criteria == {"clarity", "correctness"}

        clarity = next(s for s in loaded.scores if s.criterion == "clarity")
        assert clarity.score == 4
        assert clarity.comment == "Good"

        correctness = next(s for s in loaded.scores if s.criterion == "correctness")
        assert correctness.score == 5
        assert correctness.comment == "Excellent"

    def test_scores_are_frozen_dataclass_instances(
        self, integration_session: Session
    ) -> None:
        repo = SqlAlchemyPeerReviewRepository(integration_session)
        review = _make_review()
        review.submit(
            scores=[ReviewScore(criterion="quality", score=3)],
            overall_feedback="OK",
        )
        review.collect_events()

        repo.save(review)
        loaded = repo.find_by_id("r1")

        assert loaded is not None
        score = loaded.scores[0]
        assert isinstance(score, ReviewScore)
        # Frozen dataclass — should be immutable
        with pytest.raises(AttributeError):
            score.score = 5  # type: ignore[misc]

    def test_draft_review_has_no_scores(self, integration_session: Session) -> None:
        repo = SqlAlchemyPeerReviewRepository(integration_session)
        review = _make_review()

        repo.save(review)
        loaded = repo.find_by_id("r1")

        assert loaded is not None
        assert loaded.scores == []


# ---------------------------------------------------------------------------
# PeerReview Repository: find_by_submission
# ---------------------------------------------------------------------------


class TestPeerReviewFindBySubmission:
    """Tests for SqlAlchemyPeerReviewRepository.find_by_submission."""

    def test_returns_empty_list_when_no_reviews(
        self, integration_session: Session
    ) -> None:
        repo = SqlAlchemyPeerReviewRepository(integration_session)

        result = repo.find_by_submission("nonexistent")

        assert result == []

    def test_returns_reviews_for_submission(self, integration_session: Session) -> None:
        repo = SqlAlchemyPeerReviewRepository(integration_session)
        r1 = _make_review(review_id="r1", submission_id="s1", reviewer_id="rev1")
        r2 = _make_review(review_id="r2", submission_id="s1", reviewer_id="rev2")
        r_other = _make_review(review_id="r3", submission_id="s2", reviewer_id="rev3")

        repo.save(r1)
        repo.save(r2)
        repo.save(r_other)

        result = repo.find_by_submission("s1")

        assert len(result) == 2
        review_ids = {r.review_id for r in result}
        assert review_ids == {"r1", "r2"}

    def test_find_by_submission_loads_scores(
        self, integration_session: Session
    ) -> None:
        repo = SqlAlchemyPeerReviewRepository(integration_session)
        review = _make_review()
        review.submit(
            scores=[ReviewScore(criterion="quality", score=4)],
            overall_feedback="Good work",
        )
        review.collect_events()

        repo.save(review)
        result = repo.find_by_submission("s1")

        assert len(result) == 1
        assert len(result[0].scores) == 1
        assert result[0].scores[0].criterion == "quality"


# ---------------------------------------------------------------------------
# PeerReview Repository: upsert
# ---------------------------------------------------------------------------


class TestPeerReviewUpsert:
    """Verify that save() is idempotent (upsert semantics)."""

    def test_save_twice_updates_existing_review(
        self, integration_session: Session
    ) -> None:
        repo = SqlAlchemyPeerReviewRepository(integration_session)
        review = _make_review()

        repo.save(review)

        review.submit(
            scores=[ReviewScore(criterion="quality", score=5)],
            overall_feedback="Excellent",
        )
        review.collect_events()
        repo.save(review)

        loaded = repo.find_by_id("r1")
        assert loaded is not None
        assert loaded.status == ReviewStatus.SUBMITTED
        assert len(loaded.scores) == 1


# ---------------------------------------------------------------------------
# PeerReview Repository: reconstitution
# ---------------------------------------------------------------------------


class TestPeerReviewReconstitution:
    """Verify reconstituted reviews have clean transient state."""

    def test_reconstituted_review_has_empty_events(
        self, integration_session: Session
    ) -> None:
        repo = SqlAlchemyPeerReviewRepository(integration_session)
        review = _make_review()

        repo.save(review)
        loaded = repo.find_by_id("r1")

        assert loaded is not None
        assert loaded._events == []


# ---------------------------------------------------------------------------
# Unit of Work: extended with practice_tasks + peer_reviews
# ---------------------------------------------------------------------------


class TestUnitOfWorkPracticeTasksRepo:
    """Tests for UoW with practice_tasks repository."""

    def test_uow_exposes_practice_tasks_repo(
        self,
        integration_session_factory: sessionmaker[Session],
    ) -> None:
        uow = SqlAlchemyUnitOfWork(integration_session_factory)

        with uow:
            assert hasattr(uow, "practice_tasks")

    def test_uow_commit_persists_practice_task(
        self,
        integration_session_factory: sessionmaker[Session],
    ) -> None:
        uow = SqlAlchemyUnitOfWork(integration_session_factory)
        task = _make_task()

        with uow:
            uow.practice_tasks.save(task)
            uow.commit()

        with uow:
            loaded = uow.practice_tasks.find_by_id("t1")
            assert loaded is not None
            assert loaded.task_id == "t1"

    def test_uow_rollback_discards_practice_task(
        self,
        integration_session_factory: sessionmaker[Session],
    ) -> None:
        uow = SqlAlchemyUnitOfWork(integration_session_factory)
        task = _make_task()

        with uow:
            uow.practice_tasks.save(task)
            uow.rollback()

        with uow:
            loaded = uow.practice_tasks.find_by_id("t1")
            assert loaded is None


class TestUnitOfWorkPeerReviewsRepo:
    """Tests for UoW with peer_reviews repository."""

    def test_uow_exposes_peer_reviews_repo(
        self,
        integration_session_factory: sessionmaker[Session],
    ) -> None:
        uow = SqlAlchemyUnitOfWork(integration_session_factory)

        with uow:
            assert hasattr(uow, "peer_reviews")

    def test_uow_commit_persists_peer_review(
        self,
        integration_session_factory: sessionmaker[Session],
    ) -> None:
        uow = SqlAlchemyUnitOfWork(integration_session_factory)
        review = _make_review()

        with uow:
            uow.peer_reviews.save(review)
            uow.commit()

        with uow:
            loaded = uow.peer_reviews.find_by_id("r1")
            assert loaded is not None
            assert loaded.review_id == "r1"

    def test_uow_rollback_discards_peer_review(
        self,
        integration_session_factory: sessionmaker[Session],
    ) -> None:
        uow = SqlAlchemyUnitOfWork(integration_session_factory)
        review = _make_review()

        with uow:
            uow.peer_reviews.save(review)
            uow.rollback()

        with uow:
            loaded = uow.peer_reviews.find_by_id("r1")
            assert loaded is None


# ---------------------------------------------------------------------------
# Unit of Work: domain event publishing for new aggregates
# ---------------------------------------------------------------------------


class _SpyHandler:
    """Spy handler that records all events for assertion."""

    def __init__(self) -> None:
        self.handled: list[DomainEvent] = []

    def handle(self, event: DomainEvent) -> None:
        self.handled.append(event)


class TestUnitOfWorkPeerReviewEventPublishing:
    """Integration tests for domain event publishing for peer review aggregates."""

    def test_practice_task_events_published_after_commit(
        self,
        integration_session_factory: sessionmaker[Session],
    ) -> None:
        bus = InProcessEventBus()
        handler = _SpyHandler()
        bus.subscribe(PracticeTaskCreated, handler)

        # Create a fresh task WITH events (don't clear them)
        task = PracticeTask(
            task_id="evt-t1",
            cohort_id="c1",
            topic_id="topic1",
            creator_id="creator1",
            title="Event Test Task",
        )
        uow = SqlAlchemyUnitOfWork(integration_session_factory, event_bus=bus)

        with uow:
            uow.practice_tasks.save(task)
            assert handler.handled == []
            uow.commit()

        assert len(handler.handled) == 1
        event = handler.handled[0]
        assert isinstance(event, PracticeTaskCreated)
        assert event.task_id == "evt-t1"

    def test_peer_review_events_published_after_commit(
        self,
        integration_session_factory: sessionmaker[Session],
    ) -> None:
        bus = InProcessEventBus()
        handler = _SpyHandler()
        bus.subscribe(PeerReviewSubmitted, handler)

        review = PeerReview(
            review_id="evt-r1",
            submission_id="s1",
            reviewer_id="reviewer1",
            task_id="t1",
            cohort_id="c1",
        )
        review.submit(
            scores=[ReviewScore(criterion="quality", score=4)],
            overall_feedback="Good",
        )

        uow = SqlAlchemyUnitOfWork(integration_session_factory, event_bus=bus)

        with uow:
            uow.peer_reviews.save(review)
            assert handler.handled == []
            uow.commit()

        assert len(handler.handled) == 1
        event = handler.handled[0]
        assert isinstance(event, PeerReviewSubmitted)
        assert event.review_id == "evt-r1"

    def test_events_not_published_after_rollback(
        self,
        integration_session_factory: sessionmaker[Session],
    ) -> None:
        bus = InProcessEventBus()
        handler = _SpyHandler()
        bus.subscribe(PracticeTaskCreated, handler)

        task = PracticeTask(
            task_id="evt-t2",
            cohort_id="c1",
            topic_id="topic1",
            creator_id="creator1",
            title="Rollback Test",
        )
        uow = SqlAlchemyUnitOfWork(integration_session_factory, event_bus=bus)

        with uow:
            uow.practice_tasks.save(task)
            uow.rollback()

        assert handler.handled == []
