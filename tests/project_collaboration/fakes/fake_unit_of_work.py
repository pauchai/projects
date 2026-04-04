"""Fake in-memory implementation of UnitOfWork for testing."""

import copy

from project_collaboration.domain.project import Project
from project_collaboration.domain.project_status import ProjectStatus
from project_collaboration.domain.skill_tag import SkillTag


class _FakeProjectRepository:
    """In-memory ProjectRepository used within FakeUnitOfWork."""

    def __init__(self) -> None:
        self._storage: dict[str, Project] = {}

    def find_by_id(self, project_id: str) -> Project | None:
        return self._storage.get(project_id)

    def save(self, project: Project) -> None:
        self._storage[project.project_id] = project

    def search(
        self,
        skills: list[SkillTag] | None = None,
        keyword: str | None = None,
        status: ProjectStatus | None = None,
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
            results.append(project)
        return results

    def snapshot(self) -> dict[str, Project]:
        """Return a shallow copy of the storage for rollback support."""
        return dict(self._storage)

    def restore(self, snapshot: dict[str, Project]) -> None:
        """Restore storage from a snapshot."""
        self._storage = snapshot


class FakeUnitOfWork:
    """Fake UoW for testing: in-memory with commit/rollback semantics.

    On __enter__, snapshots current state. On commit(), keeps changes.
    On rollback() or __exit__ without commit, restores the snapshot.
    """

    def __init__(self) -> None:
        self.projects = _FakeProjectRepository()
        self.committed = False
        self._snapshot: dict[str, Project] | None = None

    def __enter__(self) -> "FakeUnitOfWork":
        self.committed = False
        self._snapshot = self.projects.snapshot()
        return self

    def __exit__(self, *args: object) -> None:
        if not self.committed:
            self.rollback()
        self._snapshot = None

    def commit(self) -> None:
        self.committed = True
        # Snapshot is discarded — changes are kept
        self._snapshot = None

    def rollback(self) -> None:
        if self._snapshot is not None:
            self.projects.restore(self._snapshot)
            self._snapshot = None
