"""CompetencyAchievementSaga — Stage 14.

Listens to ``PeerReviewSubmitted`` events and automatically checks whether
the reviewed learner has satisfied the *automatic* prerequisites for topic
competency:

1. The learner has submitted to **all** practice tasks for the topic.
2. The learner has received **at least 2 peer reviews** across those tasks.

When both conditions are met, the saga emits ``CompetencyPrerequisitesMet``
to notify the cohort that the learner is eligible for full competency
validation.

The saga does NOT create a ``TopicCompetency`` record — that still requires a
Master or Curator to call ``ValidateTopicCompetencyUseCase`` with a
``knowledge_check_score`` and ``mentor_approved=True``.

Idempotency: if a ``TopicCompetency`` record already exists for the learner
and topic, the saga emits nothing.
"""

from __future__ import annotations

from cohort_learning.domain.events import (
    CompetencyPrerequisitesMet,
    PeerReviewSubmitted,
)
from cohort_learning.domain.ports import UnitOfWork
from shared_kernel.events import DomainEvent, EventBus

_MIN_PEER_REVIEWS = 2


class CompetencyAchievementSaga:
    """Saga: auto-check competency prerequisites on each peer review.

    Constructor args:
        uow: UnitOfWork — used for all read-only repository queries.
        event_bus: EventBus — receives ``CompetencyPrerequisitesMet`` when
            prerequisites are satisfied.
    """

    def __init__(self, uow: UnitOfWork, event_bus: EventBus) -> None:
        self._uow = uow
        self._event_bus = event_bus

    def handle(self, event: DomainEvent) -> None:
        assert isinstance(event, PeerReviewSubmitted)
        self._process(event)

    # -------------------------------------------------------------------------
    # Internal processing
    # -------------------------------------------------------------------------

    def _process(self, event: PeerReviewSubmitted) -> None:
        with self._uow:
            task = self._uow.practice_tasks.find_by_id(event.task_id)
            if task is None:
                return

            submission = task.find_submission(event.submission_id)
            if submission is None:
                return

            learner_id = submission.learner_id
            topic_id = task.topic_id
            cohort_id = event.cohort_id

            # Idempotency guard: skip if already fully validated
            existing = self._uow.topic_competencies.find_by_learner_and_topic(
                learner_id, topic_id, cohort_id
            )
            if existing is not None:
                return

            # Prerequisite 1: all tasks for this topic must have a submission
            if not self._all_tasks_completed(learner_id, topic_id, cohort_id):
                return

            # Prerequisite 2: at least 2 peer reviews received across topic tasks
            if not self._enough_reviews_received(learner_id, topic_id, cohort_id):
                return

            self._event_bus.publish(
                [
                    CompetencyPrerequisitesMet(
                        cohort_id=cohort_id,
                        learner_id=learner_id,
                        topic_id=topic_id,
                    )
                ]
            )

    def _all_tasks_completed(
        self, learner_id: str, topic_id: str, cohort_id: str
    ) -> bool:
        """Return True if the learner has a submission for every topic task."""
        all_tasks = self._uow.practice_tasks.find_by_cohort(cohort_id)
        topic_tasks = [t for t in all_tasks if t.topic_id == topic_id]

        if not topic_tasks:
            return False

        return all(
            t.find_submission_by_learner(learner_id) is not None for t in topic_tasks
        )

    def _enough_reviews_received(
        self, learner_id: str, topic_id: str, cohort_id: str
    ) -> bool:
        """Return True if the learner has received >= 2 peer reviews on topic tasks."""
        all_tasks = self._uow.practice_tasks.find_by_cohort(cohort_id)
        topic_tasks = [t for t in all_tasks if t.topic_id == topic_id]

        review_count = 0
        for t in topic_tasks:
            sub = t.find_submission_by_learner(learner_id)
            if sub is not None:
                reviews = self._uow.peer_reviews.find_by_submission(sub.submission_id)
                review_count += len(reviews)

        return review_count >= _MIN_PEER_REVIEWS
