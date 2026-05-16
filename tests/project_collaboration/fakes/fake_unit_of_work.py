"""Fake in-memory implementation of UnitOfWork for testing."""

import copy

from project_collaboration.domain.feature_request import FeatureRequest
from project_collaboration.domain.feature_status import FeatureStatus
from project_collaboration.domain.project import Project
from project_collaboration.domain.project_need import ProjectNeed
from project_collaboration.domain.project_status import ProjectStatus
from project_collaboration.domain.skill_tag import SkillTag
from shared_kernel.events import DomainEvent, EventBus


class _FakeProjectRepository:
    """In-memory ProjectRepository used within FakeUnitOfWork."""

    def __init__(self, uow: "FakeUnitOfWork") -> None:
        self._storage: dict[str, Project] = {}
        self._uow = uow

    def find_by_id(self, project_id: str) -> Project | None:
        return self._storage.get(project_id)

    def save(self, project: Project) -> None:
        events = project.collect_events()
        self._uow.collect_events(events)
        self._storage[project.project_id] = project

    def search(
        self,
        skills: list[SkillTag] | None = None,
        keyword: str | None = None,
        status: ProjectStatus | None = None,
        owner_id: str | None = None,
        member_user_id: str | None = None,
    ) -> list[Project]:
        results: list[Project] = []
        for project in self._storage.values():
            if status is not None and project.status != status:
                continue
            if skills:
                skill_values = {s.value for s in skills}
                project_skill_values = {s.value for s in project.required_skills}
                if not (skill_values & project_skill_values):
                    continue
            if keyword:
                lower_keyword = keyword.lower()
                if (
                    lower_keyword not in project.title.lower()
                    and lower_keyword not in project.description.lower()
                ):
                    continue
            if owner_id is not None and project.owner_id != owner_id:
                continue
            if member_user_id is not None:
                has_active_membership = any(
                    m.user_id == member_user_id and m.is_active
                    for m in project.memberships
                )
                if not has_active_membership:
                    continue
            results.append(project)
        return results

    def snapshot(self) -> dict[str, Project]:
        """Return a deep copy of the storage for rollback support."""
        return copy.deepcopy(self._storage)

    def restore(self, snapshot: dict[str, Project]) -> None:
        """Restore storage from a snapshot."""
        self._storage = snapshot


class _FakeFeatureRequestRepository:
    """In-memory FeatureRequestRepository used within FakeUnitOfWork."""

    def __init__(self, uow: "FakeUnitOfWork") -> None:
        self._storage: dict[str, FeatureRequest] = {}
        self._uow = uow

    def find_by_id(self, request_id: str) -> FeatureRequest | None:
        return self._storage.get(request_id)

    def save(self, feature_request: FeatureRequest) -> None:
        events = feature_request.collect_events()
        self._uow.collect_events(events)
        self._storage[feature_request.request_id] = feature_request

    def find_all(
        self,
        status: FeatureStatus | None = None,
        author_id: str | None = None,
    ) -> list[FeatureRequest]:
        results: list[FeatureRequest] = []
        for fr in self._storage.values():
            if status is not None and fr.status != status:
                continue
            if author_id is not None and fr.author_id != author_id:
                continue
            results.append(fr)
        return results

    def snapshot(self) -> dict[str, FeatureRequest]:
        """Return a deep copy of the storage for rollback support."""
        return copy.deepcopy(self._storage)

    def restore(self, snapshot: dict[str, FeatureRequest]) -> None:
        """Restore storage from a snapshot."""
        self._storage = snapshot


class _FakeProjectNeedRepository:
    """In-memory ProjectNeedRepository used within FakeUnitOfWork."""

    def __init__(self) -> None:
        self._storage: dict[str, ProjectNeed] = {}

    def find_by_id(self, need_id: str) -> ProjectNeed | None:
        return self._storage.get(need_id)

    def find_by_project_id(self, project_id: str) -> list[ProjectNeed]:
        return [n for n in self._storage.values() if n.project_id == project_id]

    def save(self, need: ProjectNeed) -> None:
        self._storage[need.need_id] = need

    def snapshot(self) -> dict[str, ProjectNeed]:
        return copy.deepcopy(self._storage)

    def restore(self, snapshot: dict[str, ProjectNeed]) -> None:
        self._storage = snapshot


class FakeUnitOfWork:
    """Fake UoW for testing: in-memory with commit/rollback semantics.

    On __enter__, snapshots current state. On commit(), keeps changes.
    On rollback() or __exit__ without commit, restores the snapshot.
    Supports optional event bus for verifying event publication.
    """

    def __init__(self, event_bus: EventBus | None = None) -> None:
        self.projects = _FakeProjectRepository(self)
        self.feature_requests = _FakeFeatureRequestRepository(self)
        self.needs = _FakeProjectNeedRepository()
        self.committed = False
        self._projects_snapshot: dict[str, Project] | None = None
        self._feature_requests_snapshot: dict[str, FeatureRequest] | None = None
        self._needs_snapshot: dict[str, ProjectNeed] | None = None
        self._event_bus = event_bus
        self._pending_events: list[DomainEvent] = []

    def __enter__(self) -> "FakeUnitOfWork":
        self.committed = False
        self._projects_snapshot = self.projects.snapshot()
        self._feature_requests_snapshot = self.feature_requests.snapshot()
        self._needs_snapshot = self.needs.snapshot()
        return self

    def __exit__(self, *args: object) -> None:
        if not self.committed:
            self.rollback()
        self._projects_snapshot = None
        self._feature_requests_snapshot = None
        self._needs_snapshot = None

    def commit(self) -> None:
        self.committed = True
        # Publish events after "commit"
        if self._event_bus and self._pending_events:
            self._event_bus.publish(self._pending_events)
        self._pending_events.clear()
        # Snapshots are discarded — changes are kept
        self._projects_snapshot = None
        self._feature_requests_snapshot = None
        self._needs_snapshot = None

    def rollback(self) -> None:
        if self._projects_snapshot is not None:
            self.projects.restore(self._projects_snapshot)
            self._projects_snapshot = None
        if self._feature_requests_snapshot is not None:
            self.feature_requests.restore(self._feature_requests_snapshot)
            self._feature_requests_snapshot = None
        if self._needs_snapshot is not None:
            self.needs.restore(self._needs_snapshot)
            self._needs_snapshot = None
        self._pending_events.clear()

    def collect_events(self, events: list[DomainEvent]) -> None:
        """Accumulate domain events for publishing after commit."""
        self._pending_events.extend(events)
