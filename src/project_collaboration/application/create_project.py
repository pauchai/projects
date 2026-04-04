"""CreateProject use case."""

from project_collaboration.domain.ports import UnitOfWork
from project_collaboration.domain.project import Project
from project_collaboration.domain.skill_tag import SkillTag


class CreateProjectUseCase:
    """Creates a new project in Draft status with the creator as Owner."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(
        self,
        project_id: str,
        title: str,
        description: str,
        owner_id: str,
        required_skills: list[SkillTag],
        max_members: int | None = None,
    ) -> Project:
        with self._uow as uow:
            project = Project(
                project_id=project_id,
                title=title,
                description=description,
                owner_id=owner_id,
                required_skills=required_skills,
                max_members=max_members,
            )
            uow.projects.save(project)
            uow.commit()
            return project
