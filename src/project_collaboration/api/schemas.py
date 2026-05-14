"""Pydantic schemas for API request/response serialization."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from project_collaboration.domain.product_type import ProductType


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class CreateProjectRequest(BaseModel):
    """POST /projects"""

    project_id: str
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(default="", max_length=5000)
    required_skills: list[str] = Field(default_factory=list)
    max_members: int | None = None


class UpdateProjectRequest(BaseModel):
    """PATCH /projects/{project_id}"""

    title: str = Field(min_length=3, max_length=200)
    description: str = Field(default="", max_length=5000)
    required_skills: list[str] = Field(default_factory=list)
    max_members: int | None = None


class ApplyToProjectRequest(BaseModel):
    """POST /projects/{project_id}/applications"""

    application_id: str
    desired_role: str
    motivation: str = Field(default="", max_length=2000)
    applicant_skills: list[str] = Field(default_factory=list)


class ChangeMemberRoleRequest(BaseModel):
    """PATCH /projects/{project_id}/members/{membership_id}/role"""

    new_role: str


class SearchProjectsParams(BaseModel):
    """GET /projects/search query parameters."""

    keyword: str | None = None
    status: str | None = None
    skills: str | None = None  # comma-separated skill values


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class MembershipResponse(BaseModel):
    """Serialized Membership entity."""

    membership_id: str
    user_id: str
    project_id: str
    role: str
    is_active: bool
    joined_at: datetime


class ApplicationResponse(BaseModel):
    """Serialized ApplicationForm entity."""

    application_id: str
    applicant_id: str
    project_id: str
    desired_role: str
    motivation: str
    applicant_skills: list[str]
    status: str
    reviewed_by: str | None
    submitted_at: datetime


class ProjectResponse(BaseModel):
    """Serialized Project aggregate."""

    project_id: str
    title: str
    description: str
    owner_id: str
    required_skills: list[str]
    max_members: int | None
    status: str
    created_at: datetime
    memberships: list[MembershipResponse]
    applications: list[ApplicationResponse]


class ProjectSummaryResponse(BaseModel):
    """Lightweight project summary for search results."""

    project_id: str
    title: str
    description: str
    owner_id: str
    required_skills: list[str]
    status: str
    created_at: datetime


class MessageResponse(BaseModel):
    """Generic success/info response."""

    message: str


# ---------------------------------------------------------------------------
# Feature Request schemas
# ---------------------------------------------------------------------------


class CreateFeatureRequestRequest(BaseModel):
    """POST /features"""

    request_id: str
    title: str = Field(min_length=3, max_length=500)
    description: str = Field(min_length=1, max_length=10000)
    category: str | None = None
    priority: str | None = None


class UpdateFeatureStatusRequest(BaseModel):
    """PUT /admin/features/{request_id}/status"""

    status: str
    admin_notes: str | None = None


class FeatureRequestResponse(BaseModel):
    """Serialized FeatureRequest entity."""

    request_id: str
    author_id: str
    title: str
    description: str
    status: str
    category: str | None
    priority: str | None
    admin_notes: str
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Product schemas
# ---------------------------------------------------------------------------


class CreateProductRequest(BaseModel):
    """POST /projects/{project_id}/products"""

    product_id: str
    title: str = Field(min_length=1, max_length=300)
    product_type: ProductType
    description: str = Field(default="", max_length=5000)
    price: float | None = None
    visibility: str = "public"
    ref_id: str | None = None

    @model_validator(mode="after")
    def validate_ref_id(self) -> "CreateProductRequest":
        """course requires cohort ref_id; mentoring requires mentor user ref_id."""
        if self.product_type.requires_ref_id and not self.ref_id:
            raise ValueError(
                f"ref_id is required for product type '{self.product_type.value}'"
            )
        return self


# ---------------------------------------------------------------------------
# Fund schemas
# ---------------------------------------------------------------------------


class FundTransactionResponse(BaseModel):
    transaction_id: str
    fund_id: str
    amount: float
    source: str
    ref_id: str | None
    created_at: datetime


class FundDistributionResponse(BaseModel):
    distribution_id: str
    fund_id: str
    amount: float
    initiated_by: str
    note: str
    status: str
    created_at: datetime


class FundResponse(BaseModel):
    fund_id: str | None  # None if fund has not been created yet
    project_id: str
    balance: float
    transactions: list[FundTransactionResponse] = []
    distributions: list[FundDistributionResponse] = []


class DepositRequest(BaseModel):
    amount: float = Field(gt=0, description="Net amount to deposit (after commission)")
    source: str = Field(default="manual", max_length=50)
    ref_id: str | None = None


class DistributeRequest(BaseModel):
    amount: float = Field(gt=0, description="Fixed amount to distribute from the fund")
    note: str = Field(default="", max_length=1000)


class ProductResponse(BaseModel):
    """Serialized Product entity."""

    product_id: str
    project_id: str
    title: str
    product_type: str
    description: str
    price: float | None
    visibility: str
    is_active: bool
    ref_id: str | None
    created_at: datetime
