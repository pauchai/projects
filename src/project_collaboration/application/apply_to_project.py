"""ApplyToProject use case."""

from project_collaboration.application._helpers import get_project_or_raise
from project_collaboration.domain.ports import UnitOfWork
from project_collaboration.domain.role import ProjectRole
from project_collaboration.domain.skill_tag import SkillTag


class ApplyToProjectUseCase:
    """Submits an application to join a recruiting project."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(
        self,
        application_id: str,
        project_id: str,
        applicant_id: str,
        desired_role: ProjectRole,
        motivation: str,
        applicant_skills: list[SkillTag],
    ) -> None:
        with self._uow as uow:
            project = get_project_or_raise(uow, project_id)
            project.apply(
                application_id=application_id,
                applicant_id=applicant_id,
                desired_role=desired_role,
                motivation=motivation,
                applicant_skills=applicant_skills,
            )
            uow.projects.save(project)
            uow.commit()
