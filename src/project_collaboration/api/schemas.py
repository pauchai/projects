"""Pydantic schemas for API request/response serialization."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


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
