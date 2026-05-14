"""SQLAlchemy ORM-based repository adapters (driven adapters).

Uses SQLAlchemy ORM with Imperative Mapping (configured in ``orm.py``).
Domain classes are loaded/saved as mapped objects; the ORM handles
``__new__`` + attribute population on load, bypassing ``__init__``.

Two attributes on Project are NOT mapped by the ORM and require manual handling:
- ``required_skills`` — stored in the ``project_skill_tags`` association
  table, loaded/saved via helper methods (SkillTag is a frozen dataclass).
- ``_events`` — transient list of domain events, initialised after load.
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from project_collaboration.domain.feature_request import FeatureRequest
from project_collaboration.domain.feature_status import FeatureStatus
from project_collaboration.domain.fund import FundDistribution, FundTransaction, ProjectFund
from project_collaboration.domain.product import Product
from project_collaboration.domain.project import Project
from project_collaboration.domain.project_status import ProjectStatus
from project_collaboration.domain.skill_tag import SkillTag
from project_collaboration.infrastructure.orm import (
    feature_requests_table,
    fund_distributions_table,
    fund_transactions_table,
    project_funds_table,
    project_products_table,
    project_skill_tags_table,
)


class SqlAlchemyProjectRepository:
    """Implements ProjectRepository Protocol using SQLAlchemy ORM."""

    def __init__(self, session: Session, uow: object | None = None) -> None:
        self._session = session
        self._uow = uow

    # ------------------------------------------------------------------
    # Public interface (matches ProjectRepository Protocol)
    # ------------------------------------------------------------------

    def find_by_id(self, project_id: str) -> Project | None:
        """Load a full Project aggregate by ID, or return None."""
        project = self._session.get(
            Project,
            project_id,
            options=[
                selectinload(Project.memberships),  # type: ignore[attr-defined]
                selectinload(Project.applications),  # type: ignore[attr-defined]
            ],
        )
        if project is None:
            return None

        self._load_required_skills(project)
        self._init_transient(project)
        return project

    def save(self, project: Project) -> None:
        """Persist a Project aggregate (project + skills + memberships + applications).

        Collects domain events from the aggregate and passes them to the UoW
        for publishing after commit.
        """
        # 1. Collect domain events before merge (merge may return a different object)
        events = project.collect_events()
        if events and self._uow is not None and hasattr(self._uow, "collect_events"):
            self._uow.collect_events(events)

        # 2. Merge the aggregate (project + relationships handled by ORM)
        self._session.merge(project)
        # Flush to ensure project row exists before writing skill tags
        self._session.flush()

        # 3. Save required_skills to the association table
        self._save_required_skills(project)

    def search(
        self,
        skills: list[SkillTag] | None = None,
        keyword: str | None = None,
        status: ProjectStatus | None = None,
        owner_id: str | None = None,
        member_user_id: str | None = None,
    ) -> list[Project]:
        """Search projects with optional filters."""
        from project_collaboration.infrastructure.orm import (
            memberships_table,
            projects_table,
        )

        query = select(Project).options(
            selectinload(Project.memberships),  # type: ignore[attr-defined]
            selectinload(Project.applications),  # type: ignore[attr-defined]
        )

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

        results = self._session.scalars(query).unique().all()

        for project in results:
            self._load_required_skills(project)
            self._init_transient(project)

        return list(results)

    # ------------------------------------------------------------------
    # Private helpers for non-mapped attributes
    # ------------------------------------------------------------------

    def _load_required_skills(self, project: Project) -> None:
        """Load required_skills from the association table into the project."""
        rows = self._session.execute(
            select(project_skill_tags_table.c.skill_value).where(
                project_skill_tags_table.c.project_id == project.project_id
            )
        ).fetchall()
        project.required_skills = [SkillTag(row[0]) for row in rows]

    def _save_required_skills(self, project: Project) -> None:
        """Replace required_skills in the association table (delete + insert)."""
        self._session.execute(
            delete(project_skill_tags_table).where(
                project_skill_tags_table.c.project_id == project.project_id
            )
        )
        if project.required_skills:
            self._session.execute(
                project_skill_tags_table.insert(),
                [
                    {
                        "project_id": project.project_id,
                        "skill_value": skill.value,
                    }
                    for skill in project.required_skills
                ],
            )

    @staticmethod
    def _init_transient(project: Project) -> None:
        """Initialise transient attributes that the ORM does not populate."""
        if not hasattr(project, "_events"):
            project._events = []


class SqlAlchemyFeatureRequestRepository:
    """Implements FeatureRequestRepository Protocol using SQLAlchemy ORM."""

    def __init__(self, session: Session, uow: object | None = None) -> None:
        self._session = session
        self._uow = uow

    def find_by_id(self, request_id: str) -> FeatureRequest | None:
        """Load a FeatureRequest by ID, or return None."""
        feature_request = self._session.get(FeatureRequest, request_id)
        if feature_request is None:
            return None
        self._init_transient(feature_request)
        return feature_request

    def save(self, feature_request: FeatureRequest) -> None:
        """Persist a FeatureRequest."""
        events = feature_request.collect_events()
        if events and self._uow is not None and hasattr(self._uow, "collect_events"):
            self._uow.collect_events(events)

        self._session.merge(feature_request)
        self._session.flush()

    def find_all(
        self,
        status: FeatureStatus | None = None,
        author_id: str | None = None,
    ) -> list[FeatureRequest]:
        """Query feature requests with optional filters."""
        query = select(FeatureRequest)

        if status is not None:
            query = query.where(feature_requests_table.c.status == status)

        if author_id is not None:
            query = query.where(feature_requests_table.c.author_id == author_id)

        results = self._session.scalars(query).all()
        for fr in results:
            self._init_transient(fr)
        return list(results)

    @staticmethod
    def _init_transient(feature_request: FeatureRequest) -> None:
        """Initialise transient attributes that the ORM does not populate."""
        if not hasattr(feature_request, "_events"):
            feature_request._events = []


class SqlAlchemyProductRepository:
    """Implements ProductRepository Protocol using SQLAlchemy ORM."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def find_by_id(self, product_id: str) -> Product | None:
        return self._session.get(Product, product_id)

    def save(self, product: Product) -> None:
        self._session.merge(product)
        self._session.flush()

    def find_by_project(self, project_id: str) -> list[Product]:
        query = select(Product).where(
            project_products_table.c.project_id == project_id
        )
        return list(self._session.scalars(query).all())


class SqlAlchemyFundRepository:
    """Implements FundRepository Protocol using SQLAlchemy ORM."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def find_by_project(self, project_id: str) -> ProjectFund | None:
        query = select(ProjectFund).where(
            project_funds_table.c.project_id == project_id
        )
        return self._session.scalars(query).first()

    def save(self, fund: ProjectFund) -> None:
        self._session.merge(fund)
        self._session.flush()

    def save_transaction(self, tx: FundTransaction) -> None:
        self._session.merge(tx)
        self._session.flush()

    def save_distribution(self, dist: FundDistribution) -> None:
        self._session.merge(dist)
        self._session.flush()

    def list_transactions(self, fund_id: str) -> list[FundTransaction]:
        query = (
            select(FundTransaction)
            .where(fund_transactions_table.c.fund_id == fund_id)
            .order_by(fund_transactions_table.c.created_at.desc())
        )
        return list(self._session.scalars(query).all())

    def list_distributions(self, fund_id: str) -> list[FundDistribution]:
        query = (
            select(FundDistribution)
            .where(fund_distributions_table.c.fund_id == fund_id)
            .order_by(fund_distributions_table.c.created_at.desc())
        )
        return list(self._session.scalars(query).all())
