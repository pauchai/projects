from dataclasses import dataclass

from community.domain.community_role import CommunityRole
from shared_kernel.events import DomainEvent


@dataclass(frozen=True)
class CommunityCreated(DomainEvent):
    community_id: str
    owner_id: str
    name: str


@dataclass(frozen=True)
class CommunityUpdated(DomainEvent):
    community_id: str
    updated_fields: list[str]


@dataclass(frozen=True)
class CommunitySuspended(DomainEvent):
    community_id: str


@dataclass(frozen=True)
class CommunityArchived(DomainEvent):
    community_id: str


@dataclass(frozen=True)
class CommunityReactivated(DomainEvent):
    community_id: str


@dataclass(frozen=True)
class MemberJoined(DomainEvent):
    membership_id: str
    community_id: str
    user_id: str
    role: CommunityRole


@dataclass(frozen=True)
class MemberRoleChanged(DomainEvent):
    membership_id: str
    community_id: str
    user_id: str
    new_role: CommunityRole


@dataclass(frozen=True)
class MemberRemoved(DomainEvent):
    membership_id: str
    community_id: str
    user_id: str


@dataclass(frozen=True)
class FundDeposited(DomainEvent):
    fund_id: str
    community_id: str
    amount: str
    source: str


@dataclass(frozen=True)
class FundDistributed(DomainEvent):
    distribution_id: str
    fund_id: str
    community_id: str
    amount: str
    initiated_by: str


@dataclass(frozen=True)
class FeatureRequestSubmitted(DomainEvent):
    request_id: str
    community_id: str
    author_id: str
    title: str


@dataclass(frozen=True)
class FeatureRequestStatusChanged(DomainEvent):
    request_id: str
    community_id: str
    old_status: str
    new_status: str
