"""Repository ports and Unit of Work (driven ports) for the Cohort Learning domain."""

from typing import Protocol

from cohort_learning.domain.learning_cohort import LearningCohort
from cohort_learning.domain.peer_review import PeerReview
from cohort_learning.domain.practice_task import PracticeTask


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

    def __enter__(self) -> "UnitOfWork": ...
    def __exit__(self, *args: object) -> None: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...
