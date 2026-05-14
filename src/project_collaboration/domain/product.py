"""Product entity — a monetisable service or course offered by a project."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from project_collaboration.domain.product_type import ProductType
from project_collaboration.domain.product_visibility import ProductVisibility


class Product:
    """A product (course, consultation, onboarding, etc.) attached to a project.

    Products are the primary monetisation unit of the platform. A product may
    optionally reference an external entity (e.g. a cohort) via ``ref_id``.
    """

    def __init__(
        self,
        product_id: str,
        project_id: str,
        title: str,
        product_type: ProductType,
        *,
        description: str = "",
        price: Decimal | None = None,
        visibility: ProductVisibility = ProductVisibility.PUBLIC,
        is_active: bool = True,
        ref_id: str | None = None,
        created_at: datetime | None = None,
    ) -> None:
        self.product_id = product_id
        self.project_id = project_id
        self.title = title
        self.product_type = product_type
        self.description = description
        self.price = price
        self.visibility = visibility
        self.is_active = is_active
        self.ref_id = ref_id
        self.created_at = created_at or datetime.now(timezone.utc)

    def deactivate(self) -> None:
        """Mark the product as inactive (soft-delete)."""
        if not self.is_active:
            raise ValueError("Product is already inactive")
        self.is_active = False

    def update_price(self, price: Decimal | None) -> None:
        """Update the product price. None means free."""
        if price is not None and price < Decimal("0"):
            raise ValueError("Price cannot be negative")
        self.price = price

    @property
    def is_free(self) -> bool:
        """Return True if the product has no price set."""
        return self.price is None or self.price == Decimal("0")
