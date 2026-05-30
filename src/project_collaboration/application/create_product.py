"""CreateProduct use case — adds a new product to a project."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from project_collaboration.domain.ports import UnitOfWork
from project_collaboration.domain.product import Product
from project_collaboration.domain.product_type import ProductType
from project_collaboration.domain.product_visibility import ProductVisibility
from project_collaboration.domain.role import ProjectRole


@dataclass
class CreateProductCommand:
    product_id: str
    project_id: str
    title: str
    product_type: ProductType
    requester_id: str
    description: str = ""
    price: Decimal | None = None
    visibility: ProductVisibility = ProductVisibility.PUBLIC
    ref_id: str | None = None


class CreateProductUseCase:
    """Create a new product for a project.

    Only the project owner or an admin member may create products.
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, cmd: CreateProductCommand) -> Product:
        with self._uow as uow:
            project = uow.projects.find_by_id(cmd.project_id)
            if project is None:
                raise LookupError(f"Project {cmd.project_id!r} not found")

            is_manager = any(
                m.user_id == cmd.requester_id
                and m.is_active
                and m.role in (ProjectRole.OWNER, ProjectRole.ADMIN)
                for m in project.memberships
            )
            if not is_manager:
                raise PermissionError("Only project owner or admin can create products")

            product = Product(
                product_id=cmd.product_id,
                project_id=cmd.project_id,
                title=cmd.title,
                product_type=cmd.product_type,
                description=cmd.description,
                price=cmd.price,
                visibility=cmd.visibility,
                ref_id=cmd.ref_id,
            )
            uow.products.save(product)
            uow.commit()
            return product
