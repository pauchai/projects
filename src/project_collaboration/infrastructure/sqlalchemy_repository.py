"""SQLAlchemy Core-based ProjectRepository (driven adapter).

Uses SQLAlchemy Core (Table + connection.execute) rather than ORM mapping,
so that domain classes stay completely free of infrastructure concerns.
Reconstitution bypasses ``__init__`` via ``object.__new__`` + direct attribute
assignment, avoiding validation re-runs on load.
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from project_collaboration.domain.application_form import (
    ApplicationForm,
    ApplicationStatus,
)
from project_collaboration.domain.membership import Membership
from project_collaboration.domain.project import Project
from project_collaboration.domain.project_status import ProjectStatus
from project_collaboration.domain.role import ProjectRole
from project_collaboration.domain.skill_tag import SkillTag
from project_collaboration.infrastructure.orm import (
    applications_table,
    memberships_table,
    project_skill_tags_table,
    projects_table,
)


class SqlAlchemyProjectRepository:
    """Implements ProjectRepository Protocol using SQLAlchemy Core queries."""

    def __init__(self, session: Session) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # Public interface (matches ProjectRepository Protocol)
    # ------------------------------------------------------------------

    def find_by_id(self, project_id: str) -> Project | None:
        """Load a full Project aggregate by ID, or return None."""
        conn = self._session.connection()

        # 1. Load project row
        row = conn.execute(
            select(projects_table).where(projects_table.c.project_id == project_id)
        ).first()
        if row is None:
            return None

        # 2. Load related data
        skill_rows = conn.execute(
            select(project_skill_tags_table).where(
                project_skill_tags_table.c.project_id == project_id
            )
        ).fetchall()

        membership_rows = conn.execute(
            select(memberships_table).where(
                memberships_table.c.project_id == project_id
            )
        ).fetchall()

        application_rows = conn.execute(
            select(applications_table).where(
                applications_table.c.project_id == project_id
            )
        ).fetchall()

        return self._reconstitute_project(
            row, skill_rows, membership_rows, application_rows
        )

    def save(self, project: Project) -> None:
        """Upsert a Project aggregate (project + skills + memberships + applications)."""
        conn = self._session.connection()

        # 1. Upsert project row
        stmt = pg_insert(projects_table).values(
            project_id=project.project_id,
            title=project.title,
            description=project.description,
            owner_id=project.owner_id,
            max_members=project.max_members,
            status=project.status,
            previous_status=project._previous_status,
            created_at=project.created_at,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["project_id"],
            set_={
                "title": stmt.excluded.title,
                "description": stmt.excluded.description,
                "owner_id": stmt.excluded.owner_id,
                "max_members": stmt.excluded.max_members,
                "status": stmt.excluded.status,
                "previous_status": stmt.excluded.previous_status,
                "created_at": stmt.excluded.created_at,
            },
        )
        conn.execute(stmt)

        # 2. Replace skill tags (delete + insert)
        conn.execute(
            delete(project_skill_tags_table).where(
                project_skill_tags_table.c.project_id == project.project_id
            )
        )
        if project.required_skills:
            conn.execute(
                project_skill_tags_table.insert(),
                [
                    {
                        "project_id": project.project_id,
                        "skill_value": skill.value,
                    }
                    for skill in project.required_skills
                ],
            )

        # 3. Upsert memberships
        for m in project.memberships:
            m_stmt = pg_insert(memberships_table).values(
                membership_id=m.membership_id,
                user_id=m.user_id,
                project_id=m.project_id,
                role=m.role,
                is_active=m.is_active,
                joined_at=m.joined_at,
            )
            m_stmt = m_stmt.on_conflict_do_update(
                index_elements=["membership_id"],
                set_={
                    "role": m_stmt.excluded.role,
                    "is_active": m_stmt.excluded.is_active,
                },
            )
            conn.execute(m_stmt)

        # 4. Upsert applications
        for a in project.applications:
            a_stmt = pg_insert(applications_table).values(
                application_id=a.application_id,
                applicant_id=a.applicant_id,
                project_id=a.project_id,
                desired_role=a.desired_role,
                motivation=a.motivation,
                applicant_skills=[s.value for s in a.applicant_skills],
                status=a.status,
                reviewed_by=a.reviewed_by,
                submitted_at=a.submitted_at,
            )
            a_stmt = a_stmt.on_conflict_do_update(
                index_elements=["application_id"],
                set_={
                    "status": a_stmt.excluded.status,
                    "reviewed_by": a_stmt.excluded.reviewed_by,
                },
            )
            conn.execute(a_stmt)

    def search(
        self,
        skills: list[SkillTag] | None = None,
        keyword: str | None = None,
        status: ProjectStatus | None = None,
        owner_id: str | None = None,
        member_user_id: str | None = None,
    ) -> list[Project]:
        """Search projects with optional filters."""
        conn = self._session.connection()

        query = select(projects_table)

        if status is not None:
            query = query.where(projects_table.c.status == status)

        if keyword is not None:
            pattern = f"%{keyword.lower()}%"
            query = query.where(
                projects_table.c.title.ilike(pattern)
                | projects_table.c.description.ilike(pattern)
            )

        if skills:
            skill_values = [s.value for s in skills]
            # Subquery: projects that have at least one matching skill
            skill_subq = (
                select(project_skill_tags_table.c.project_id)
                .where(project_skill_tags_table.c.skill_value.in_(skill_values))
                .distinct()
                .subquery()
            )
            query = query.where(projects_table.c.project_id.in_(select(skill_subq)))

        if owner_id is not None:
            query = query.where(projects_table.c.owner_id == owner_id)

        if member_user_id is not None:
            member_subq = (
                select(memberships_table.c.project_id)
                .where(
                    memberships_table.c.user_id == member_user_id,
                    memberships_table.c.is_active.is_(True),
                )
                .distinct()
                .subquery()
            )
            query = query.where(projects_table.c.project_id.in_(select(member_subq)))

        project_rows = conn.execute(query).fetchall()

        results: list[Project] = []
        for row in project_rows:
            pid = row.project_id
            skill_rows = conn.execute(
                select(project_skill_tags_table).where(
                    project_skill_tags_table.c.project_id == pid
                )
            ).fetchall()
            membership_rows = conn.execute(
                select(memberships_table).where(memberships_table.c.project_id == pid)
            ).fetchall()
            application_rows = conn.execute(
                select(applications_table).where(applications_table.c.project_id == pid)
            ).fetchall()
            results.append(
                self._reconstitute_project(
                    row, skill_rows, membership_rows, application_rows
                )
            )

        return results

    # ------------------------------------------------------------------
    # Private reconstitution helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _reconstitute_project(
        row: object,
        skill_rows: list,
        membership_rows: list,
        application_rows: list,
    ) -> Project:
        """Rebuild a Project aggregate from raw DB rows, bypassing __init__."""
        project = object.__new__(Project)
        project.project_id = row.project_id  # type: ignore[attr-defined]
        project.title = row.title  # type: ignore[attr-defined]
        project.description = row.description  # type: ignore[attr-defined]
        project.owner_id = row.owner_id  # type: ignore[attr-defined]
        project.max_members = row.max_members  # type: ignore[attr-defined]
        project.status = row.status  # type: ignore[attr-defined]
        project._previous_status = row.previous_status  # type: ignore[attr-defined]
        project.created_at = row.created_at  # type: ignore[attr-defined]
        project._events = []

        # Reconstitute skills
        project.required_skills = [
            SkillTag(r.skill_value)
            for r in skill_rows  # type: ignore[attr-defined]
        ]

        # Reconstitute memberships
        project.memberships = [
            SqlAlchemyProjectRepository._reconstitute_membership(r)
            for r in membership_rows
        ]

        # Reconstitute applications
        project.applications = [
            SqlAlchemyProjectRepository._reconstitute_application(r)
            for r in application_rows
        ]

        return project

    @staticmethod
    def _reconstitute_membership(row: object) -> Membership:
        """Rebuild a Membership entity from a raw DB row."""
        m = object.__new__(Membership)
        m.membership_id = row.membership_id  # type: ignore[attr-defined]
        m.user_id = row.user_id  # type: ignore[attr-defined]
        m.project_id = row.project_id  # type: ignore[attr-defined]
        m.role = row.role  # type: ignore[attr-defined]
        m.is_active = row.is_active  # type: ignore[attr-defined]
        m.joined_at = row.joined_at  # type: ignore[attr-defined]
        return m

    @staticmethod
    def _reconstitute_application(row: object) -> ApplicationForm:
        """Rebuild an ApplicationForm entity from a raw DB row."""
        a = object.__new__(ApplicationForm)
        a.application_id = row.application_id  # type: ignore[attr-defined]
        a.applicant_id = row.applicant_id  # type: ignore[attr-defined]
        a.project_id = row.project_id  # type: ignore[attr-defined]
        a.desired_role = row.desired_role  # type: ignore[attr-defined]
        a.motivation = row.motivation  # type: ignore[attr-defined]
        a.status = row.status  # type: ignore[attr-defined]
        a.reviewed_by = row.reviewed_by  # type: ignore[attr-defined]
        a.submitted_at = row.submitted_at  # type: ignore[attr-defined]

        # applicant_skills stored as JSON list of strings → SkillTag objects
        raw_skills = row.applicant_skills or []  # type: ignore[attr-defined]
        a.applicant_skills = [SkillTag(s) for s in raw_skills]

        return a
