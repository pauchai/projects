"""Shared test factories for the cohort_learning domain.

All factories produce domain objects with sensible defaults.
Use ``save_cohort(uow, cohort)`` to persist into a FakeUnitOfWork.
"""

from __future__ import annotations

from datetime import datetime, UTC
from decimal import Decimal

from cohort_learning.domain.cohort_status import CohortStatus
from cohort_learning.domain.helper_metrics import HelperMetrics
from cohort_learning.domain.learning_cohort import LearningCohort
from cohort_learning.domain.module_curator import ModuleCurator
from cohort_learning.domain.module_progression import ModuleProgression
from cohort_learning.domain.peer_review import PeerReview
from cohort_learning.domain.practice_task import PracticeTask
from cohort_learning.domain.topic import Topic
from cohort_learning.domain.topic_expert import TopicExpert
from tests.cohort_learning.fakes.fake_unit_of_work import FakeUnitOfWork


def make_module(**overrides: object) -> ModuleProgression:
    """Create a ModuleProgression with sensible defaults."""
    defaults: dict = dict(
        module_id="mod1",
        title="Frontend Basics",
        master_id="master1",
    )
    defaults.update(overrides)
    return ModuleProgression(**defaults)


def make_module_with_topics(
    topic_count: int = 3, **overrides: object
) -> ModuleProgression:
    """Create a ModuleProgression with N topics."""
    module = make_module(**overrides)
    for i in range(topic_count):
        module.add_topic(
            Topic(topic_id=f"t{i + 1}", title=f"Topic {i + 1}", position=i)
        )
    return module


def make_cohort(**overrides: object) -> LearningCohort:
    """Create a LearningCohort in Forming status with sensible defaults."""
    defaults: dict = dict(
        cohort_id="c1",
        master_id="master1",
        module_id="mod1",
    )
    defaults.update(overrides)
    return LearningCohort(**defaults)


def make_active_cohort(learner_count: int = 5, **overrides: object) -> LearningCohort:
    """Create a cohort in Active status with N enrolled learners."""
    cohort = make_cohort(**overrides)
    for i in range(learner_count):
        cohort.enrol_learner(
            membership_id=f"mem{i + 1}",
            learner_id=f"learner{i + 1}",
        )
    cohort.activate()
    cohort.collect_events()
    return cohort


def save_cohort(uow: FakeUnitOfWork, cohort: LearningCohort) -> None:
    """Persist a cohort into the FakeUnitOfWork (opens UoW, saves, commits)."""
    with uow:
        uow.cohorts.save(cohort)
        uow.commit()


# --- Practice task factories ---


def make_task(**overrides: object) -> PracticeTask:
    """Create a PracticeTask in Draft status with sensible defaults."""
    defaults: dict = dict(
        task_id="task1",
        cohort_id="c1",
        topic_id="t1",
        creator_id="master1",
        title="Build a REST API",
    )
    defaults.update(overrides)
    return PracticeTask(**defaults)


def make_active_task(**overrides: object) -> PracticeTask:
    """Create a PracticeTask in Active status (ready to accept submissions)."""
    task = make_task(**overrides)
    task.activate()
    task.collect_events()
    return task


def save_task(uow: FakeUnitOfWork, task: PracticeTask) -> None:
    """Persist a task into the FakeUnitOfWork (opens UoW, saves, commits)."""
    with uow:
        uow.practice_tasks.save(task)
        uow.commit()


# --- Peer review factories ---


def make_review(**overrides: object) -> PeerReview:
    """Create a PeerReview in Draft status with sensible defaults."""
    defaults: dict = dict(
        review_id="rev1",
        submission_id="sub1",
        reviewer_id="learner2",
        task_id="task1",
        cohort_id="c1",
    )
    defaults.update(overrides)
    return PeerReview(**defaults)


def save_review(uow: FakeUnitOfWork, review: PeerReview) -> None:
    """Persist a review into the FakeUnitOfWork (opens UoW, saves, commits)."""
    with uow:
        uow.peer_reviews.save(review)
        uow.commit()


# --- Partner progression factories ---


def create_cohort(
    cohort_id: str = "cohort-1",
    master_id: str = "master-1",
    module_id: str = "module-1",
    status: CohortStatus = CohortStatus.FORMING,
) -> LearningCohort:
    """Create a LearningCohort with explicit parameters.

    Note: To activate a cohort, you must enrol at least 5 learners first.
    """
    cohort = LearningCohort(
        cohort_id=cohort_id,
        master_id=master_id,
        module_id=module_id,
    )
    # Note: Activation requires 5 learners, so status changes must happen after enrollment
    # Only set status to FORMING by default
    cohort.collect_events()  # Clear events
    return cohort


def create_topic_expert(
    expert_id: str,
    learner_id: str,
    topic_id: str,
    cohort_id: str,
    validator_id: str,
    validated_at: datetime | None = None,
) -> TopicExpert:
    """Create a TopicExpert with explicit parameters."""
    return TopicExpert(
        expert_id=expert_id,
        learner_id=learner_id,
        topic_id=topic_id,
        cohort_id=cohort_id,
        validated_at=validated_at or datetime.now(UTC),
        validator_id=validator_id,
    )


def create_helper_metrics(
    learner_id: str,
    cohort_id: str,
    learners_helped: int = 0,
    questions_answered: int = 0,
    tasks_reviewed: int = 0,
    average_satisfaction: Decimal | None = None,
    updated_at: datetime | None = None,
) -> HelperMetrics:
    """Create HelperMetrics with explicit parameters."""
    return HelperMetrics(
        learner_id=learner_id,
        cohort_id=cohort_id,
        learners_helped=learners_helped,
        questions_answered=questions_answered,
        tasks_reviewed=tasks_reviewed,
        average_satisfaction=average_satisfaction,
        updated_at=updated_at or datetime.now(UTC),
    )


def create_module_curator(
    curator_id: str,
    learner_id: str,
    module_id: str,
    cohort_id: str,
    promoted_by: str,
    promoted_at: datetime | None = None,
) -> ModuleCurator:
    """Create a ModuleCurator with explicit parameters."""
    return ModuleCurator(
        curator_id=curator_id,
        learner_id=learner_id,
        module_id=module_id,
        cohort_id=cohort_id,
        promoted_at=promoted_at or datetime.now(UTC),
        promoted_by=promoted_by,
    )
