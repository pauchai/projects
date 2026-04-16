"""PracticeTask aggregate root — a task within a cohort requiring learner practice."""

from __future__ import annotations

from datetime import datetime, timezone

from cohort_learning.domain.events import (
    PracticeTaskCreated,
    TaskSubmissionCreated,
)
from cohort_learning.domain.task_status import TaskStatus
from cohort_learning.domain.task_submission import TaskSubmission
from shared_kernel.events import DomainEvent


class PracticeTask:
    """Aggregate root for a practice task scoped to a topic within a cohort.

    Manages the task lifecycle (Draft → Active → Closed) and owns
    the collection of learner submissions.

    Business rules:
    - Only the master or a module curator may create a task (enforced by use case).
    - Submissions are accepted only while the task is Active.
    - A learner may submit only once per task (resubmit via revision workflow).
    - The task creator cannot submit to their own task.
    """

    def __init__(
        self,
        task_id: str,
        cohort_id: str,
        topic_id: str,
        creator_id: str,
        title: str,
        description: str = "",
    ) -> None:
        if not title.strip():
            raise ValueError("Practice task title must not be empty")

        self.task_id = task_id
        self.cohort_id = cohort_id
        self.topic_id = topic_id
        self.creator_id = creator_id
        self.title = title
        self.description = description
        self.status: TaskStatus = TaskStatus.DRAFT
        self.created_at: datetime = datetime.now(timezone.utc)

        self.submissions: list[TaskSubmission] = []
        self._events: list[DomainEvent] = []

        self._emit(
            PracticeTaskCreated(
                task_id=task_id,
                cohort_id=cohort_id,
                topic_id=topic_id,
                creator_id=creator_id,
                title=title,
            )
        )

    # -------------------------------------------------------------------------
    # Event helpers
    # -------------------------------------------------------------------------

    def collect_events(self) -> list[DomainEvent]:
        """Return and clear uncommitted domain events."""
        events = list(self._events)
        self._events.clear()
        return events

    def _emit(self, event: DomainEvent) -> None:
        self._events.append(event)

    # -------------------------------------------------------------------------
    # Status transitions
    # -------------------------------------------------------------------------

    def _transition_to(self, target: TaskStatus) -> None:
        if not self.status.can_transition_to(target):
            raise ValueError(
                f"Cannot transition from {self.status.value} to {target.value}"
            )
        self.status = target

    def activate(self) -> None:
        """Draft → Active. Makes the task available for submissions."""
        self._transition_to(TaskStatus.ACTIVE)

    def close(self) -> None:
        """Draft/Active → Closed. No more submissions accepted."""
        self._transition_to(TaskStatus.CLOSED)

    # -------------------------------------------------------------------------
    # Submissions
    # -------------------------------------------------------------------------

    def add_submission(
        self,
        submission_id: str,
        learner_id: str,
        content: str,
    ) -> TaskSubmission:
        """Add a learner submission to this task.

        Raises ValueError if:
        - Task is not Active.
        - The learner is the task creator.
        - The learner has already submitted.
        """
        if self.status != TaskStatus.ACTIVE:
            raise ValueError("Submissions are only accepted while task is active")

        if learner_id == self.creator_id:
            raise ValueError("Task creator cannot submit to their own task")

        if any(s.learner_id == learner_id for s in self.submissions):
            raise ValueError(
                f"Learner '{learner_id}' has already submitted to this task"
            )

        submission = TaskSubmission(
            submission_id=submission_id,
            task_id=self.task_id,
            learner_id=learner_id,
            content=content,
        )
        self.submissions.append(submission)

        self._emit(
            TaskSubmissionCreated(
                submission_id=submission_id,
                task_id=self.task_id,
                learner_id=learner_id,
                cohort_id=self.cohort_id,
            )
        )

        return submission

    # -------------------------------------------------------------------------
    # Queries
    # -------------------------------------------------------------------------

    def find_submission(self, submission_id: str) -> TaskSubmission | None:
        """Find a submission by its id. Returns None if not found."""
        for s in self.submissions:
            if s.submission_id == submission_id:
                return s
        return None

    def find_submission_by_learner(self, learner_id: str) -> TaskSubmission | None:
        """Find the submission by a specific learner. Returns None if not found."""
        for s in self.submissions:
            if s.learner_id == learner_id:
                return s
        return None

    @property
    def submission_count(self) -> int:
        """Return the number of submissions."""
        return len(self.submissions)
