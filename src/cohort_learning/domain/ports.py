"""Repository ports and Unit of Work (driven ports) for the Cohort Learning domain."""

from typing import Protocol

from cohort_learning.domain.helper_metrics import HelperMetrics
from cohort_learning.domain.learning_cohort import LearningCohort
from cohort_learning.domain.module_curator import ModuleCurator
from cohort_learning.domain.peer_review import PeerReview
from cohort_learning.domain.practice_task import PracticeTask
from cohort_learning.domain.topic_expert import TopicExpert


class CohortRepository(Protocol):
    """Port for persisting and querying LearningCohorts."""

    def find_by_id(self, cohort_id: str) -> LearningCohort | None: ...

    def save(self, cohort: LearningCohort) -> None: ...


class PracticeTaskRepository(Protocol):
    """Port for persisting and querying PracticeTasks."""

    def find_by_id(self, task_id: str) -> PracticeTask | None: ...

    def save(self, task: PracticeTask) -> None: ...

    def find_by_cohort(self, cohort_id: str) -> list[PracticeTask]: ...


class PeerReviewRepository(Protocol):
    """Port for persisting and querying PeerReviews."""

    def find_by_id(self, review_id: str) -> PeerReview | None: ...

    def save(self, review: PeerReview) -> None: ...

    def find_by_submission(self, submission_id: str) -> list[PeerReview]: ...


class TopicExpertRepository(Protocol):
    """Port for persisting and querying TopicExperts."""

    def find_by_id(self, expert_id: str) -> TopicExpert | None: ...

    def save(self, expert: TopicExpert) -> None: ...

    def find_by_learner_and_topic(
        self, learner_id: str, topic_id: str
    ) -> TopicExpert | None: ...

    def find_by_topic(self, topic_id: str) -> list[TopicExpert]: ...


class HelperMetricsRepository(Protocol):
    """Port for persisting and querying HelperMetrics."""

    def find_by_learner(
        self, learner_id: str, cohort_id: str
    ) -> HelperMetrics | None: ...

    def save(self, metrics: HelperMetrics) -> None: ...


class ModuleCuratorRepository(Protocol):
    """Port for persisting and querying ModuleCurators."""

    def find_by_id(self, curator_id: str) -> ModuleCurator | None: ...

    def save(self, curator: ModuleCurator) -> None: ...

    def find_by_learner_and_module(
        self, learner_id: str, module_id: str
    ) -> ModuleCurator | None: ...

    def find_by_module(self, module_id: str) -> list[ModuleCurator]: ...


class UnitOfWork(Protocol):
    """Driven port: coordinates atomic persistence of domain changes.

    Application Services manage the UoW lifecycle (enter, commit/rollback, exit).
    The domain layer defines this contract; infrastructure provides the real
    implementation. Tests use a FakeUnitOfWork.

    Usage::

        with uow:
            cohort = uow.cohorts.find_by_id("c1")
            cohort.activate()
            uow.cohorts.save(cohort)
            uow.commit()
    """

    cohorts: CohortRepository
    practice_tasks: PracticeTaskRepository
    peer_reviews: PeerReviewRepository
    topic_experts: TopicExpertRepository
    helper_metrics: HelperMetricsRepository
    module_curators: ModuleCuratorRepository

    def __enter__(self) -> "UnitOfWork": ...
    def __exit__(self, *args: object) -> None: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...
