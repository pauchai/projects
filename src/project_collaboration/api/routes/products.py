"""Product routes: GET/POST /projects/{project_id}/products."""

from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status

from project_collaboration.api.dependencies import get_current_user_id, get_uow
from project_collaboration.api.schemas import CreateProductRequest, ProductResponse
from project_collaboration.application.create_product import (
    CreateProductCommand,
    CreateProductUseCase,
)
from project_collaboration.application.list_products import ListProjectProductsUseCase
from project_collaboration.domain.product import Product
from project_collaboration.domain.product_type import ProductType
from project_collaboration.domain.product_visibility import ProductVisibility

router = APIRouter(prefix="/projects", tags=["products"])


def _serialize_product(p: Product) -> ProductResponse:
    return ProductResponse(
        product_id=p.product_id,
        project_id=p.project_id,
        title=p.title,
        product_type=p.product_type.value,
        description=p.description,
        price=float(p.price) if p.price is not None else None,
        visibility=p.visibility.value,
        is_active=p.is_active,
        ref_id=p.ref_id,
        created_at=p.created_at,
    )


@router.get(
    "/{project_id}/products",
    response_model=list[ProductResponse],
    summary="List products for a project",
)
def list_products(
    project_id: str,
    uow: object = Depends(get_uow),
) -> list[ProductResponse]:
    use_case = ListProjectProductsUseCase(uow)
    products = use_case.execute(project_id)
    return [_serialize_product(p) for p in products]


@router.post(
    "/{project_id}/products",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a product for a project",
)
def create_product(
    project_id: str,
    body: CreateProductRequest,
    uow: object = Depends(get_uow),
    current_user_id: str = Depends(get_current_user_id),
) -> ProductResponse:
    try:
        product_type = ProductType(body.product_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid product_type: {body.product_type!r}",
        )

    try:
        visibility = ProductVisibility(body.visibility)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid visibility: {body.visibility!r}",
        )

    cmd = CreateProductCommand(
        product_id=body.product_id,
        project_id=project_id,
        title=body.title,
        product_type=product_type,
        requester_id=current_user_id,
        description=body.description,
        price=Decimal(str(body.price)) if body.price is not None else None,
        visibility=visibility,
        ref_id=body.ref_id,
    )

    try:
        use_case = CreateProductUseCase(uow)
        product = use_case.execute(cmd)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))

    return _serialize_product(product)
