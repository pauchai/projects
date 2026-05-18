"""Internal routes for service-to-service calls (MCP server, etc.).

All routes require a service token (MCP_SERVICE_TOKEN) and the X-User-ID header
to impersonate the target user.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from project_collaboration.api.dependencies import (
    AuthenticationError,
    get_service_user_id,
    get_uow,
)
from project_collaboration.api.schemas import (
    CreateProjectRequest,
    ProjectResponse,
    ProjectSummaryResponse,
)
from project_collaboration.application.create_project import CreateProjectUseCase
from project_collaboration.application.search_projects import SearchProjectsUseCase
from project_collaboration.domain.project_status import ProjectStatus
from project_collaboration.domain.skill_tag import SkillTag
from project_collaboration.infrastructure.sqlalchemy_unit_of_work import (
    SqlAlchemyUnitOfWork,
)
from project_collaboration.api.routes.projects import (
    _project_to_response,
    _project_to_summary,
)

router = APIRouter(prefix="/internal", tags=["internal"])


@router.get("/projects", response_model=list[ProjectSummaryResponse])
def list_projects(
    owner_id: str,
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> list[ProjectSummaryResponse]:
    """List all projects owned by a specific user.

    Requires: Authorization: Bearer <MCP_SERVICE_TOKEN>
    Header:   X-User-ID: <target_user_id>
    """
    use_case = SearchProjectsUseCase(uow)
    results = use_case.execute(owner_id=owner_id)
    return [_project_to_summary(p) for p in results]


@router.post("/projects", status_code=201, response_model=ProjectResponse)
def create_project(
    body: CreateProjectRequest,
    caller_id: str = Depends(get_service_user_id),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> ProjectResponse:
    """Create a project on behalf of the user specified in X-User-ID.

    Requires: Authorization: Bearer <MCP_SERVICE_TOKEN>
    Header:   X-User-ID: <target_user_id>
    """
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