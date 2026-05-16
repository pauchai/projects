"""Project routes: REST endpoints for the Project Collaboration API."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse

from project_collaboration.api.dependencies import get_current_user_id, get_uow
from project_collaboration.api.schemas import (
    ApplyToProjectRequest,
    ChangeMemberRoleRequest,
    CreateProjectNeedRequest,
    CreateProjectRequest,
    DocsSyncResponse,
    MessageResponse,
    ProjectNeedResponse,
    ProjectResponse,
    ProjectSummaryResponse,
    SetDocsRepoUrlRequest,
    UpdateProjectRequest,
)
from project_collaboration.application.apply_to_project import ApplyToProjectUseCase
from project_collaboration.application.change_project_status import (
    ActivateProjectUseCase,
    CancelProjectUseCase,
    CompleteProjectUseCase,
    ResumeProjectUseCase,
    SuspendProjectUseCase,
)
from project_collaboration.application.close_project_need import CloseProjectNeedUseCase
from project_collaboration.application.create_project import CreateProjectUseCase
from project_collaboration.application.create_project_need import (
    CreateProjectNeedCommand,
    CreateProjectNeedUseCase,
)
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
from project_collaboration.application.update_project import UpdateProjectUseCase
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
        docs_repo_url=getattr(project, "docs_repo_url", None),
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


@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: str,
    body: UpdateProjectRequest,
    caller_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> ProjectResponse:
    """Update a project. Only the owner can update."""
    use_case = UpdateProjectUseCase(uow)
    project = use_case.execute(
        project_id=project_id,
        caller_id=caller_id,
        title=body.title,
        description=body.description,
        required_skills=[SkillTag(s) for s in body.required_skills],
        max_members=body.max_members,
    )
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


# ---------------------------------------------------------------------------
# Docs repo URL & sync helpers
# ---------------------------------------------------------------------------


def _docs_volume_path(project_id: str) -> Path:
    base = Path(os.environ.get("VOLUMES_BASE_PATH", "./volumes"))
    return base / "projects" / project_id


def _safe_docs_file(volume: Path, rel_path: str) -> Path:
    """Resolve a relative path inside a docs volume; raise 400 on path traversal."""
    target = (volume / rel_path).resolve()
    if not str(target).startswith(str(volume.resolve())):
        raise HTTPException(status_code=400, detail="Invalid file path")
    return target


# ---------------------------------------------------------------------------
# Docs repo URL management
# ---------------------------------------------------------------------------


@router.patch("/{project_id}/docs-repo-url", response_model=ProjectResponse)
def set_docs_repo_url(
    project_id: str,
    body: SetDocsRepoUrlRequest,
    caller_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> ProjectResponse:
    """Set or update the docs git repo URL for a project.

    Only the project owner may update this field.
    """
    with uow as u:
        project = u.projects.find_by_id(project_id)
        if project is None:
            raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")
        if not project.is_owner(caller_id):
            raise HTTPException(status_code=403, detail="Only the project owner may set docs_repo_url")
        project.docs_repo_url = body.docs_repo_url
        u.projects.save(project)
        u.commit()
        return _project_to_response(project)


# ---------------------------------------------------------------------------
# Docs git sync
# ---------------------------------------------------------------------------


@router.post("/{project_id}/sync-docs", response_model=DocsSyncResponse)
def sync_docs_volume(
    project_id: str,
    caller_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> DocsSyncResponse:
    """Clone or pull the project's git docs repo into the local volume."""
    from cohort_learning.infrastructure.git_sync import GitVolumeSync  # noqa: PLC0415

    with uow as u:
        project = u.projects.find_by_id(project_id)
        if project is None:
            raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")
        if not project.is_owner(caller_id):
            raise HTTPException(status_code=403, detail="Only the project owner may trigger a sync")
        docs_repo_url = getattr(project, "docs_repo_url", None)
        if not docs_repo_url:
            raise HTTPException(status_code=422, detail=f"Project '{project_id}' has no docs_repo_url configured")

    base = Path(os.environ.get("VOLUMES_BASE_PATH", "./volumes"))
    syncer = GitVolumeSync(volumes_base_path=base)
    try:
        volume_path = syncer.sync_project(project_id=project_id, repo_url=docs_repo_url)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return DocsSyncResponse(message="sync complete", path=str(volume_path))


# ---------------------------------------------------------------------------
# Docs file tree (listing)
# ---------------------------------------------------------------------------


@router.get("/{project_id}/docs")
def get_docs_tree(
    project_id: str,
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> dict:
    """Return a sorted list of all files in the project docs volume.

    Paths are relative to the volume root, e.g. ``["README.md", "guides/setup.md"]``.
    Ignores hidden files and the ``.git`` directory.
    """
    with uow as u:
        project = u.projects.find_by_id(project_id)
        if project is None:
            raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")

    volume = _docs_volume_path(project_id)
    if not volume.exists():
        raise HTTPException(
            status_code=404,
            detail="Docs volume not found — trigger a sync first",
        )

    files: list[str] = []
    for dirpath, dirnames, filenames in os.walk(volume):
        # Skip hidden dirs (including .git) in-place so os.walk won't descend into them
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        rel_dir = Path(dirpath).relative_to(volume)
        for filename in sorted(filenames):
            if filename.startswith("."):
                continue
            rel_file = rel_dir / filename
            files.append(str(rel_file))

    return {"files": files}


# ---------------------------------------------------------------------------
# Docs file serving (Markdown)
# ---------------------------------------------------------------------------


@router.get("/{project_id}/docs/{file_path:path}", response_class=PlainTextResponse)
def get_docs_file(
    project_id: str,
    file_path: str,
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> str:
    """Return raw file content (Markdown) from the project's local docs volume.

    ``file_path`` is relative to the volume root, e.g. ``README.md``.
    Path traversal attempts are rejected.
    """
    with uow as u:
        project = u.projects.find_by_id(project_id)
        if project is None:
            raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")

    volume = _docs_volume_path(project_id)
    if not volume.exists():
        raise HTTPException(
            status_code=404,
            detail="Docs volume not found — trigger a sync first",
        )

    target = _safe_docs_file(volume, file_path)
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail=f"File '{file_path}' not found in docs volume")

    return target.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Project Needs endpoints
# ---------------------------------------------------------------------------


def _need_to_response(need: object) -> ProjectNeedResponse:
    return ProjectNeedResponse(
        need_id=need.need_id,  # type: ignore[attr-defined]
        project_id=need.project_id,  # type: ignore[attr-defined]
        role=need.role.value,  # type: ignore[attr-defined]
        description=need.description,  # type: ignore[attr-defined]
        skills=need.skills,  # type: ignore[attr-defined]
        slots=need.slots,  # type: ignore[attr-defined]
        status=need.status.value,  # type: ignore[attr-defined]
        created_by=need.created_by,  # type: ignore[attr-defined]
        created_at=need.created_at,  # type: ignore[attr-defined]
    )


@router.get("/{project_id}/needs", response_model=list[ProjectNeedResponse])
def list_project_needs(
    project_id: str,
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> list[ProjectNeedResponse]:
    """List all open/filled needs for a project. Public endpoint."""
    with uow as u:
        project = u.projects.find_by_id(project_id)
        if project is None:
            raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")
        needs = u.needs.find_by_project_id(project_id)
    return [_need_to_response(n) for n in needs]


@router.post("/{project_id}/needs", response_model=ProjectNeedResponse, status_code=201)
def create_project_need(
    project_id: str,
    body: CreateProjectNeedRequest,
    caller_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> ProjectNeedResponse:
    """Post a new open position. Any active project member can create one."""
    try:
        role = ProjectRole(body.role)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid role '{body.role}'")

    use_case = CreateProjectNeedUseCase(uow)
    try:
        need_id = use_case.execute(
            CreateProjectNeedCommand(
                project_id=project_id,
                caller_id=caller_id,
                role=role,
                description=body.description,
                skills=body.skills,
                slots=body.slots,
            )
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    with uow as u:
        need = u.needs.find_by_id(need_id)
    return _need_to_response(need)


@router.patch("/{project_id}/needs/{need_id}/close", response_model=MessageResponse)
def close_project_need(
    project_id: str,
    need_id: str,
    caller_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> MessageResponse:
    """Close an open project need."""
    use_case = CloseProjectNeedUseCase(uow)
    try:
        use_case.execute(need_id=need_id, caller_id=caller_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return MessageResponse(message="Need closed successfully")
