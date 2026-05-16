"""Public needs router — GET /needs returns all open needs across all projects."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from project_collaboration.api.dependencies import get_uow
from project_collaboration.api.schemas import PublicNeedResponse
from project_collaboration.domain.project_need import ProjectNeed
from project_collaboration.infrastructure.orm import project_needs_table
from project_collaboration.infrastructure.sqlalchemy_repository import (
    SqlAlchemyProjectNeedRepository,
)
from project_collaboration.infrastructure.sqlalchemy_unit_of_work import (
    SqlAlchemyUnitOfWork,
)

router = APIRouter(prefix="/needs", tags=["needs"])


@router.get("", response_model=list[PublicNeedResponse])
def list_open_needs(
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> list[PublicNeedResponse]:
    """Return all open project needs across the platform (no auth required)."""
    from project_collaboration.infrastructure.orm import projects_table

    with uow:
        session: Session = uow._session  # type: ignore[attr-defined]
        query = (
            select(
                project_needs_table.c.need_id,
                project_needs_table.c.project_id,
                project_needs_table.c.role,
                project_needs_table.c.description,
                project_needs_table.c.skills,
                project_needs_table.c.slots,
                project_needs_table.c.created_at,
                projects_table.c.title.label("project_title"),
            )
            .join(
                projects_table,
                project_needs_table.c.project_id == projects_table.c.project_id,
            )
            .where(project_needs_table.c.status == "open")
            .order_by(project_needs_table.c.created_at.desc())
        )
        rows = session.execute(query).mappings().all()

    import json

    result: list[PublicNeedResponse] = []
    for row in rows:
        skills = row["skills"]
        if isinstance(skills, str):
            try:
                skills = json.loads(skills)
            except Exception:
                skills = []
        result.append(
            PublicNeedResponse(
                need_id=row["need_id"],
                project_id=row["project_id"],
                project_title=row["project_title"],
                role=row["role"],
                description=row["description"],
                skills=skills or [],
                slots=row["slots"],
                created_at=row["created_at"],
            )
        )
    return result
