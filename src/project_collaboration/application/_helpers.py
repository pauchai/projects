"""Shared helper functions for application-layer use cases."""

from project_collaboration.domain.ports import UnitOfWork
from project_collaboration.domain.project import Project


def get_project_or_raise(uow: UnitOfWork, project_id: str) -> Project:
    """Fetch a project by ID or raise LookupError."""
    project = uow.projects.find_by_id(project_id)
    if project is None:
        raise LookupError(f"Project {project_id} not found")
    return project


def require_management_rights(project: Project, caller_id: str) -> None:
    """Raise PermissionError if caller lacks management rights on the project."""
    if not project.has_management_rights(caller_id):
        raise PermissionError("Caller lacks management rights for this operation")
