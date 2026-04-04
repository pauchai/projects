"""Repository ports and Unit of Work (driven ports) for the Project Collaboration domain."""

from typing import Protocol

from project_collaboration.domain.project import Project
from project_collaboration.domain.project_status import ProjectStatus
from project_collaboration.domain.skill_tag import SkillTag


class ProjectRepository(Protocol):
    """Port for persisting and querying Projects."""

    def find_by_id(self, project_id: str) -> Project | None: ...

    def save(self, project: Project) -> None: ...

    def search(
        self,
        skills: list[SkillTag] | None = None,
        keyword: str | None = None,
        status: ProjectStatus | None = None,
    ) -> list[Project]: ...


class UnitOfWork(Protocol):
    """Driven port: coordinates atomic persistence of domain changes.

    Application Services manage the UoW lifecycle (enter, commit/rollback, exit).
    The domain layer defines this contract; infrastructure provides the real
    implementation (e.g., SQLAlchemy session). Tests use a FakeUnitOfWork.

    Usage::

        with uow:
            project = uow.projects.find_by_id("p1")
            project.publish()
            uow.projects.save(project)
            uow.commit()
    """

    projects: ProjectRepository

    def __enter__(self) -> "UnitOfWork": ...
    def __exit__(self, *args: object) -> None: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...
