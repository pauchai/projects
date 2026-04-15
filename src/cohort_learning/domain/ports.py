"""Repository ports and Unit of Work (driven ports) for the Cohort Learning domain."""

from typing import Protocol

from cohort_learning.domain.learning_cohort import LearningCohort


class CohortRepository(Protocol):
    """Port for persisting and querying LearningCohorts."""

    def find_by_id(self, cohort_id: str) -> LearningCohort | None: ...

    def save(self, cohort: LearningCohort) -> None: ...


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

    def __enter__(self) -> "UnitOfWork": ...
    def __exit__(self, *args: object) -> None: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...
