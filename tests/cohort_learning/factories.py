"""Shared test factories for the cohort_learning domain.

All factories produce domain objects with sensible defaults.
Use ``save_cohort(uow, cohort)`` to persist into a FakeUnitOfWork.
"""

from __future__ import annotations

from cohort_learning.domain.learning_cohort import LearningCohort
from cohort_learning.domain.module_progression import ModuleProgression
from cohort_learning.domain.topic import Topic
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
