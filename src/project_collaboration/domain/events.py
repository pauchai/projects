"""Domain events for the Project Collaboration bounded context."""

from dataclasses import dataclass

from project_collaboration.domain.role import ProjectRole
from shared_kernel.events import DomainEvent


# --- Project lifecycle events ---


@dataclass(frozen=True)
class ProjectCreated(DomainEvent):
    project_id: str
    owner_id: str
    title: str


@dataclass(frozen=True)
class ProjectPublished(DomainEvent):
    project_id: str


@dataclass(frozen=True)
class ProjectActivated(DomainEvent):
    project_id: str


@dataclass(frozen=True)
class ProjectSuspended(DomainEvent):
    project_id: str


@dataclass(frozen=True)
class ProjectResumed(DomainEvent):
    project_id: str


@dataclass(frozen=True)
class ProjectCompleted(DomainEvent):
    project_id: str


@dataclass(frozen=True)
class ProjectCancelled(DomainEvent):
    project_id: str


# --- Application events ---


@dataclass(frozen=True)
class ApplicationSubmitted(DomainEvent):
    application_id: str
    project_id: str
    applicant_id: str


@dataclass(frozen=True)
class ApplicationAccepted(DomainEvent):
    application_id: str
    project_id: str
    applicant_id: str


@dataclass(frozen=True)
class ApplicationRejected(DomainEvent):
    application_id: str
    project_id: str
    applicant_id: str


# --- Member events ---


@dataclass(frozen=True)
class MemberJoined(DomainEvent):
    membership_id: str
    project_id: str
    user_id: str
    role: ProjectRole


@dataclass(frozen=True)
class MemberRoleChanged(DomainEvent):
    membership_id: str
    project_id: str
    new_role: ProjectRole


@dataclass(frozen=True)
class MemberRemoved(DomainEvent):
    membership_id: str
    project_id: str
    user_id: str
