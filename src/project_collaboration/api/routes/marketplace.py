"""Marketplace router — GET /marketplace returns all active public products."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from project_collaboration.api.dependencies import get_uow
from project_collaboration.api.schemas import MarketplaceProductResponse
from project_collaboration.infrastructure.orm import project_products_table
from project_collaboration.infrastructure.sqlalchemy_unit_of_work import (
    SqlAlchemyUnitOfWork,
)

router = APIRouter(prefix="/marketplace", tags=["marketplace"])


@router.get("", response_model=list[MarketplaceProductResponse])
def list_marketplace_products(
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> list[MarketplaceProductResponse]:
    """Return all active public products across the platform (no auth required)."""
    from project_collaboration.infrastructure.orm import projects_table

    with uow:
        session: Session = uow._session  # type: ignore[attr-defined]
        query = (
            select(
                project_products_table.c.product_id,
                project_products_table.c.project_id,
                project_products_table.c.title,
                project_products_table.c.product_type,
                project_products_table.c.description,
                project_products_table.c.created_at,
                projects_table.c.title.label("project_title"),
            )
            .join(
                projects_table,
                project_products_table.c.project_id == projects_table.c.project_id,
            )
            .where(
                project_products_table.c.is_active.is_(True),
                project_products_table.c.visibility == "public",
            )
            .order_by(project_products_table.c.created_at.desc())
        )
        rows = session.execute(query).mappings().all()

    return [
        MarketplaceProductResponse(
            product_id=row["product_id"],
            project_id=row["project_id"],
            project_title=row["project_title"],
            title=row["title"],
            product_type=str(row["product_type"].value)
            if hasattr(row["product_type"], "value")
            else str(row["product_type"]),
            description=row["description"],
            created_at=row["created_at"],
        )
        for row in rows
    ]
