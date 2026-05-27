from __future__ import annotations

import uuid
from datetime import datetime, timezone

from community.domain.community_membership import CommunityMembership
from community.domain.community_role import CommunityRole
from community.domain.community_status import CommunityStatus
from community.domain.events import (
    CommunityArchived,
    CommunityCreated,
    CommunityReactivated,
    CommunitySuspended,
    CommunityUpdated,
    DomainEvent,
    MemberJoined,
    MemberRemoved,
    MemberRoleChanged,
)

MIN_NAME_LENGTH = 2
MAX_NAME_LENGTH = 200
MAX_DESCRIPTION_LENGTH = 5000


class Community:
    def __init__(
        self,
        community_id: str,
        name: str,
        description: str,
        owner_id: str,
        avatar_url: str | None = None,
    ) -> None:
        if len(name) < MIN_NAME_LENGTH or len(name) > MAX_NAME_LENGTH:
            raise ValueError(
                f"Name must be between {MIN_NAME_LENGTH} and {MAX_NAME_LENGTH} characters"
            )
        if len(description) > MAX_DESCRIPTION_LENGTH:
            raise ValueError(
                f"Description must not exceed {MAX_DESCRIPTION_LENGTH} characters"
            )

        self.community_id = community_id
        self.name = name
        self.description = description
        self.owner_id = owner_id
        self.avatar_url = avatar_url
        self.status = CommunityStatus.ACTIVE
        self.created_at: datetime = datetime.now(timezone.utc)

        self.memberships: list[CommunityMembership] = []
        self._events: list[DomainEvent] = []

        owner_membership = CommunityMembership(
            membership_id=str(uuid.uuid4()),
            community_id=community_id,
            user_id=owner_id,
            role=CommunityRole.OWNER,
        )
        self.memberships.append(owner_membership)

        self._emit(
            CommunityCreated(
                community_id=community_id,
                owner_id=owner_id,
                name=name,
            )
        )

    def collect_events(self) -> list[DomainEvent]:
        events = list(self._events)
        self._events.clear()
        return events

    def _emit(self, event: DomainEvent) -> None:
        self._events.append(event)

    def update_profile(
        self,
        name: str | None = None,
        description: str | None = None,
        avatar_url: str | None = None,
    ) -> None:
        if name is not None:
            if len(name) < MIN_NAME_LENGTH or len(name) > MAX_NAME_LENGTH:
                raise ValueError(
                    f"Name must be between {MIN_NAME_LENGTH} and {MAX_NAME_LENGTH} characters"
                )
            self.name = name
        if description is not None:
            if len(description) > MAX_DESCRIPTION_LENGTH:
                raise ValueError(
                    f"Description must not exceed {MAX_DESCRIPTION_LENGTH} characters"
                )
            self.description = description
        self.avatar_url = avatar_url if avatar_url is not None else self.avatar_url

        changed = [f for f in ("name", "description", "avatar_url") if locals().get(f) is not None]
        self._emit(CommunityUpdated(community_id=self.community_id, updated_fields=changed))

    def suspend(self) -> None:
        if not self.status.can_transition_to(CommunityStatus.SUSPENDED):
            raise ValueError(f"Cannot suspend community in status {self.status.value}")
        self.status = CommunityStatus.SUSPENDED
        self._emit(CommunitySuspended(community_id=self.community_id))

    def reactivate(self) -> None:
        if not self.status.can_transition_to(CommunityStatus.ACTIVE):
            raise ValueError(f"Cannot reactivate community in status {self.status.value}")
        self.status = CommunityStatus.ACTIVE
        self._emit(CommunityReactivated(community_id=self.community_id))

    def archive(self) -> None:
        if not self.status.can_transition_to(CommunityStatus.ARCHIVED):
            raise ValueError(f"Cannot archive community in status {self.status.value}")
        self.status = CommunityStatus.ARCHIVED
        self._emit(CommunityArchived(community_id=self.community_id))

    def add_member(
        self,
        membership_id: str,
        user_id: str,
        role: CommunityRole = CommunityRole.MEMBER,
    ) -> CommunityMembership:
        if any(m.user_id == user_id and m.is_active for m in self.memberships):
            raise ValueError(f"User {user_id} is already a member")

        membership = CommunityMembership(
            membership_id=membership_id,
            community_id=self.community_id,
            user_id=user_id,
            role=role,
        )
        self.memberships.append(membership)

        self._emit(
            MemberJoined(
                membership_id=membership_id,
                community_id=self.community_id,
                user_id=user_id,
                role=role,
            )
        )
        return membership

    def remove_member(self, user_id: str) -> None:
        membership = self._find_active_membership(user_id)
        if membership is None:
            raise ValueError(f"User {user_id} is not an active member")
        if membership.role == CommunityRole.OWNER:
            raise ValueError("Cannot remove the owner of a community")
        membership.deactivate()
        self._emit(
            MemberRemoved(
                membership_id=membership.membership_id,
                community_id=self.community_id,
                user_id=user_id,
            )
        )

    def change_member_role(self, user_id: str, new_role: CommunityRole) -> None:
        membership = self._find_active_membership(user_id)
        if membership is None:
            raise ValueError(f"User {user_id} is not an active member")
        old_role = membership.role
        membership.change_role(new_role)
        self._emit(
            MemberRoleChanged(
                membership_id=membership.membership_id,
                community_id=self.community_id,
                user_id=user_id,
                new_role=new_role,
            )
        )

    def _find_active_membership(self, user_id: str) -> CommunityMembership | None:
        for m in self.memberships:
            if m.user_id == user_id and m.is_active:
                return m
        return None
