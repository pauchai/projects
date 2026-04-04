"""Project routes: REST endpoints for the Project Collaboration API."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from project_collaboration.api.dependencies import get_current_user_id, get_uow
from project_collaboration.api.schemas import (
    ApplyToProjectRequest,
    ChangeMemberRoleRequest,
    CreateProjectRequest,
    MessageResponse,
    ProjectResponse,
    ProjectSummaryResponse,
)
from project_collaboration.application.apply_to_project import ApplyToProjectUseCase
from project_collaboration.application.change_project_status import (
    ActivateProjectUseCase,
    CancelProjectUseCase,
    CompleteProjectUseCase,
    ResumeProjectUseCase,
    SuspendProjectUseCase,
)
from project_collaboration.application.create_project import CreateProjectUseCase
from project_collaboration.application.manage_member import (
    ChangeMemberRoleUseCase,
    RemoveMemberUseCase,
)
from project_collaboration.application.publish_project import PublishProjectUseCase
from project_collaboration.application.review_application import (
    AcceptApplicationUseCase,
    RejectApplicationUseCase,
)
from project_collaboration.application.search_projects import SearchProjectsUseCase
from project_collaboration.domain.project import Project
from project_collaboration.domain.project_status import ProjectStatus
from project_collaboration.domain.role import ProjectRole
from project_collaboration.domain.skill_tag import SkillTag
from project_collaboration.infrastructure.sqlalchemy_unit_of_work import (
    SqlAlchemyUnitOfWork,
)

router = APIRouter(prefix="/projects", tags=["projects"])


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------


def _project_to_response(project: Project) -> ProjectResponse:
    return ProjectResponse(
        project_id=project.project_id,
        title=project.title,
        description=project.description,
        owner_id=project.owner_id,
        required_skills=[s.value for s in project.required_skills],
        max_members=project.max_members,
        status=project.status.value,
        created_at=project.created_at,
        memberships=[
            {
                "membership_id": m.membership_id,
                "user_id": m.user_id,
                "project_id": m.project_id,
                "role": m.role.value,
                "is_active": m.is_active,
                "joined_at": m.joined_at,
            }
            for m in project.memberships
        ],
        applications=[
            {
                "application_id": a.application_id,
                "applicant_id": a.applicant_id,
                "project_id": a.project_id,
                "desired_role": a.desired_role.value,
                "motivation": a.motivation,
                "applicant_skills": [s.value for s in a.applicant_skills],
                "status": a.status.value,
                "reviewed_by": a.reviewed_by,
                "submitted_at": a.submitted_at,
            }
            for a in project.applications
        ],
    )


def _project_to_summary(project: Project) -> ProjectSummaryResponse:
    return ProjectSummaryResponse(
        project_id=project.project_id,
        title=project.title,
        description=project.description,
        owner_id=project.owner_id,
        required_skills=[s.value for s in project.required_skills],
        status=project.status.value,
        created_at=project.created_at,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("", status_code=201, response_model=ProjectResponse)
def create_project(
    body: CreateProjectRequest,
    caller_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> ProjectResponse:
    """Create a new project. The caller becomes the owner."""
    use_case = CreateProjectUseCase(uow)
    project = use_case.execute(
        project_id=body.project_id,
        title=body.title,
        description=body.description,
        owner_id=caller_id,
        required_skills=[SkillTag(s) for s in body.required_skills],
        max_members=body.max_members,
    )
    return _project_to_response(project)


@router.get("/search", response_model=list[ProjectSummaryResponse])
def search_projects(
    keyword: str | None = None,
    status: str | None = None,
    skills: str | None = None,
    owner_id: str | None = None,
    member_user_id: str | None = None,
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> list[ProjectSummaryResponse]:
    """Search projects with optional filters."""
    use_case = SearchProjectsUseCase(uow)

    parsed_status: ProjectStatus | None = None
    if status is not None and status != "all":
        parsed_status = ProjectStatus(status)

    parsed_skills: list[SkillTag] | None = None
    if skills is not None:
        parsed_skills = [SkillTag(s.strip()) for s in skills.split(",") if s.strip()]

    results = use_case.execute(
        keyword=keyword,
        status=parsed_status,
        skills=parsed_skills,
        owner_id=owner_id,
        member_user_id=member_user_id,
    )
    return [_project_to_summary(p) for p in results]


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: str,
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> ProjectResponse:
    """Get a project by ID."""
    with uow:
        project = uow.projects.find_by_id(project_id)
        if project is None:
            raise LookupError(f"Project {project_id} not found")
        return _project_to_response(project)


@router.post("/{project_id}/publish", response_model=MessageResponse)
def publish_project(
    project_id: str,
    caller_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> MessageResponse:
    """Publish a project (Draft -> Recruiting)."""
    use_case = PublishProjectUseCase(uow)
    use_case.execute(project_id=project_id, caller_id=caller_id)
    return MessageResponse(message="Project published")


@router.post(
    "/{project_id}/applications", status_code=201, response_model=MessageResponse
)
def apply_to_project(
    project_id: str,
    body: ApplyToProjectRequest,
    caller_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> MessageResponse:
    """Submit an application to join a project."""
    use_case = ApplyToProjectUseCase(uow)
    use_case.execute(
        application_id=body.application_id,
        project_id=project_id,
        applicant_id=caller_id,
        desired_role=ProjectRole(body.desired_role),
        motivation=body.motivation,
        applicant_skills=[SkillTag(s) for s in body.applicant_skills],
    )
    return MessageResponse(message="Application submitted")


@router.post(
    "/{project_id}/applications/{application_id}/accept",
    response_model=MessageResponse,
)
def accept_application(
    project_id: str,
    application_id: str,
    caller_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> MessageResponse:
    """Accept an application."""
    use_case = AcceptApplicationUseCase(uow)
    use_case.execute(
        project_id=project_id,
        application_id=application_id,
        caller_id=caller_id,
    )
    return MessageResponse(message="Application accepted")


@router.post(
    "/{project_id}/applications/{application_id}/reject",
    response_model=MessageResponse,
)
def reject_application(
    project_id: str,
    application_id: str,
    caller_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> MessageResponse:
    """Reject an application."""
    use_case = RejectApplicationUseCase(uow)
    use_case.execute(
        project_id=project_id,
        application_id=application_id,
        caller_id=caller_id,
    )
    return MessageResponse(message="Application rejected")


@router.patch(
    "/{project_id}/members/{membership_id}/role",
    response_model=MessageResponse,
)
def change_member_role(
    project_id: str,
    membership_id: str,
    body: ChangeMemberRoleRequest,
    caller_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> MessageResponse:
    """Change a member's role."""
    use_case = ChangeMemberRoleUseCase(uow)
    use_case.execute(
        project_id=project_id,
        membership_id=membership_id,
        new_role=ProjectRole(body.new_role),
        caller_id=caller_id,
    )
    return MessageResponse(message="Member role changed")


@router.delete(
    "/{project_id}/members/{membership_id}",
    response_model=MessageResponse,
)
def remove_member(
    project_id: str,
    membership_id: str,
    caller_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> MessageResponse:
    """Remove a member from a project."""
    use_case = RemoveMemberUseCase(uow)
    use_case.execute(
        project_id=project_id,
        membership_id=membership_id,
        caller_id=caller_id,
    )
    return MessageResponse(message="Member removed")


@router.post("/{project_id}/activate", response_model=MessageResponse)
def activate_project(
    project_id: str,
    caller_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> MessageResponse:
    """Activate a project (Recruiting -> Active)."""
    use_case = ActivateProjectUseCase(uow)
    use_case.execute(project_id=project_id, caller_id=caller_id)
    return MessageResponse(message="Project activated")


@router.post("/{project_id}/suspend", response_model=MessageResponse)
def suspend_project(
    project_id: str,
    caller_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> MessageResponse:
    """Suspend a project."""
    use_case = SuspendProjectUseCase(uow)
    use_case.execute(project_id=project_id, caller_id=caller_id)
    return MessageResponse(message="Project suspended")


@router.post("/{project_id}/resume", response_model=MessageResponse)
def resume_project(
    project_id: str,
    caller_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> MessageResponse:
    """Resume a suspended project."""
    use_case = ResumeProjectUseCase(uow)
    use_case.execute(project_id=project_id, caller_id=caller_id)
    return MessageResponse(message="Project resumed")


@router.post("/{project_id}/complete", response_model=MessageResponse)
def complete_project(
    project_id: str,
    caller_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> MessageResponse:
    """Complete a project (Active -> Completed)."""
    use_case = CompleteProjectUseCase(uow)
    use_case.execute(project_id=project_id, caller_id=caller_id)
    return MessageResponse(message="Project completed")


@router.post("/{project_id}/cancel", response_model=MessageResponse)
def cancel_project(
    project_id: str,
    caller_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> MessageResponse:
    """Cancel a project."""
    use_case = CancelProjectUseCase(uow)
    use_case.execute(project_id=project_id, caller_id=caller_id)
    return MessageResponse(message="Project cancelled")
