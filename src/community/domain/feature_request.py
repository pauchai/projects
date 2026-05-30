from __future__ import annotations

from datetime import datetime, timezone

from community.domain.events import (
    DomainEvent,
    FeatureRequestStatusChanged,
    FeatureRequestSubmitted,
)
from community.domain.feature_status import FeatureStatus

MIN_TITLE_LENGTH = 3
MAX_TITLE_LENGTH = 500
MAX_DESCRIPTION_LENGTH = 10000


class FeatureRequest:
    def __init__(
        self,
        request_id: str,
        community_id: str,
        author_id: str,
        title: str,
        description: str,
        category: str | None = None,
        priority: str | None = None,
    ) -> None:
        if len(title) < MIN_TITLE_LENGTH or len(title) > MAX_TITLE_LENGTH:
            raise ValueError(
                f"Title must be between {MIN_TITLE_LENGTH} and "
                f"{MAX_TITLE_LENGTH} characters"
            )
        if len(description) > MAX_DESCRIPTION_LENGTH:
            raise ValueError(
                f"Description must not exceed {MAX_DESCRIPTION_LENGTH} characters"
            )

        self.request_id = request_id
        self.community_id = community_id
        self.author_id = author_id
        self.title = title
        self.description = description
        self.status = FeatureStatus.SUBMITTED
        self.category = category
        self.priority = priority
        self.admin_notes: str = ""
        self.metadata: dict = {}
        self.created_at: datetime = datetime.now(timezone.utc)
        self.updated_at: datetime = datetime.now(timezone.utc)

        self._events: list[DomainEvent] = []

        self._emit(
            FeatureRequestSubmitted(
                request_id=request_id,
                community_id=community_id,
                author_id=author_id,
                title=title,
            )
        )

    def collect_events(self) -> list[DomainEvent]:
        events = list(self._events)
        self._events.clear()
        return events

    def _emit(self, event: DomainEvent) -> None:
        self._events.append(event)

    def change_status(self, target: FeatureStatus) -> None:
        if not self.status.can_transition_to(target):
            raise ValueError(
                f"Cannot transition from {self.status.value} to {target.value}"
            )
        old_status = self.status
        self.status = target
        self.updated_at = datetime.now(timezone.utc)
        self._emit(
            FeatureRequestStatusChanged(
                request_id=self.request_id,
                community_id=self.community_id,
                old_status=old_status.value,
                new_status=target.value,
            )
        )

    def set_admin_notes(self, notes: str) -> None:
        self.admin_notes = notes
        self.updated_at = datetime.now(timezone.utc)
