"""Shared test factories for creating Project aggregates at various lifecycle stages.

All factories produce domain objects with sensible defaults.
Use ``save_project(uow, project)`` to persist into a FakeUnitOfWork.
"""

from __future__ import annotations

from project_collaboration.domain.project import Project
from project_collaboration.domain.role import ProjectRole
from project_collaboration.domain.skill_tag import SkillTag
from tests.project_collaboration.fakes.fake_unit_of_work import FakeUnitOfWork


def make_project(**overrides: object) -> Project:
    """Create a Project in Draft status with sensible defaults, overridable."""
    defaults: dict = dict(
        project_id="p1",
        title="Test Project",
        description="A test project description.",
        owner_id="owner1",
        required_skills=[SkillTag("python")],
        max_members=None,
    )
    defaults.update(overrides)
    return Project(**defaults)


def make_recruiting_project(**overrides: object) -> Project:
    """Create a project in Recruiting status."""
    p = make_project(**overrides)
    p.publish()
    p.collect_events()
    return p


def make_active_project(**overrides: object) -> Project:
    """Create a project in Active status."""
    p = make_recruiting_project(**overrides)
    p.activate()
    p.collect_events()
    return p


def make_project_with_application(
    max_members: int | None = None,
    **overrides: object,
) -> Project:
    """Create a recruiting project with one pending application (a1 from u2)."""
    if max_members is not None:
        overrides.setdefault("max_members", max_members)
    p = make_recruiting_project(**overrides)
    p.apply(
        application_id="a1",
        applicant_id="u2",
        desired_role=ProjectRole.MEMBER,
        motivation="I want to join.",
        applicant_skills=[SkillTag("python")],
    )
    p.collect_events()
    return p


def make_project_with_member(**overrides: object) -> tuple[Project, str]:
    """Create a recruiting project with an accepted member (u2).

    Returns (project, membership_id of the new member).
    """
    p = make_project_with_application(**overrides)
    p.accept_application(application_id="a1", reviewed_by=p.owner_id)
    p.collect_events()
    member = [m for m in p.memberships if m.user_id == "u2"][0]
    return p, member.membership_id


def save_project(uow: FakeUnitOfWork, project: Project) -> None:
    """Persist a project into the FakeUnitOfWork (opens UoW, saves, commits)."""
    with uow:
        uow.projects.save(project)
        uow.commit()
