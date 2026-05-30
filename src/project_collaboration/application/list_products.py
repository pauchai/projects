"""ListProjectProducts use case — returns all products for a given project."""

from __future__ import annotations

from project_collaboration.domain.ports import UnitOfWork
from project_collaboration.domain.product import Product


class ListProjectProductsUseCase:
    """Return the list of products belonging to a project.

    Both public and members-only products are returned; visibility filtering
    is the responsibility of the API / presentation layer.
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, project_id: str) -> list[Product]:
        with self._uow as uow:
            return uow.products.find_by_project(project_id)
