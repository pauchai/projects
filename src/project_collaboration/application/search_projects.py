"""SearchProjects use case: read-only query for discovering projects."""

from project_collaboration.domain.ports import UnitOfWork
from project_collaboration.domain.project import Project
from project_collaboration.domain.project_status import ProjectStatus
from project_collaboration.domain.skill_tag import SkillTag


class SearchProjectsUseCase:
    """Returns projects matching optional skill, keyword, and status filters.

    Read-only query — no domain events, no state changes.
    Default status filter is Recruiting.
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(
        self,
        skills: list[SkillTag] | None = None,
        keyword: str | None = None,
        status: ProjectStatus | None = ProjectStatus.RECRUITING,
        owner_id: str | None = None,
        member_user_id: str | None = None,
    ) -> list[Project]:
        with self._uow as uow:
            return uow.projects.search(
                skills=skills,
                keyword=keyword,
                status=status,
                owner_id=owner_id,
                member_user_id=member_user_id,
            )
