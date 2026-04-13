"""UpdateProject use case."""

from project_collaboration.domain.ports import UnitOfWork
from project_collaboration.domain.project import Project
from project_collaboration.domain.skill_tag import SkillTag


class UpdateProjectUseCase:
    """Updates an existing project's details."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(
        self,
        project_id: str,
        caller_id: str,
        title: str,
        description: str,
        required_skills: list[SkillTag],
        max_members: int | None = None,
    ) -> Project:
        with self._uow as uow:
            project = uow.projects.find_by_id(project_id)
            if project is None:
                raise LookupError(f"Project {project_id} not found")

            if not project.is_owner(caller_id):
                raise PermissionError("Only the project owner can update this project")

            project.update(
                title=title,
                description=description,
                required_skills=required_skills,
                max_members=max_members,
            )
            uow.projects.save(project)
            uow.commit()
            return project
