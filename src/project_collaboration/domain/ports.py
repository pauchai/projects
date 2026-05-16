"""Repository ports and Unit of Work (driven ports) for the Project Collaboration domain."""

from typing import Protocol

from project_collaboration.domain.feature_request import FeatureRequest
from project_collaboration.domain.feature_status import FeatureStatus
from project_collaboration.domain.fund import FundDistribution, FundTransaction, ProjectFund
from project_collaboration.domain.product import Product
from project_collaboration.domain.project import Project
from project_collaboration.domain.project_need import ProjectNeed
from project_collaboration.domain.project_status import ProjectStatus
from project_collaboration.domain.skill_tag import SkillTag


class ProjectRepository(Protocol):
    """Port for persisting and querying Projects."""

    def find_by_id(self, project_id: str) -> Project | None: ...

    def save(self, project: Project) -> None: ...

    def search(
        self,
        skills: list[SkillTag] | None = None,
        keyword: str | None = None,
        status: ProjectStatus | None = None,
        owner_id: str | None = None,
        member_user_id: str | None = None,
    ) -> list[Project]: ...


class ProductRepository(Protocol):
    """Port for persisting and querying Products."""

    def find_by_id(self, product_id: str) -> Product | None: ...

    def save(self, product: Product) -> None: ...

    def find_by_project(self, project_id: str) -> list[Product]: ...


class FeatureRequestRepository(Protocol):
    """Port for persisting and querying FeatureRequests."""

    def find_by_id(self, request_id: str) -> FeatureRequest | None: ...

    def save(self, feature_request: FeatureRequest) -> None: ...

    def find_all(
        self,
        status: FeatureStatus | None = None,
        author_id: str | None = None,
    ) -> list[FeatureRequest]: ...


class FundRepository(Protocol):
    """Port for persisting and querying ProjectFund aggregates."""

    def find_by_project(self, project_id: str) -> ProjectFund | None: ...

    def save(self, fund: ProjectFund) -> None: ...

    def save_transaction(self, tx: FundTransaction) -> None: ...

    def save_distribution(self, dist: FundDistribution) -> None: ...

    def list_transactions(self, fund_id: str) -> list[FundTransaction]: ...

    def list_distributions(self, fund_id: str) -> list[FundDistribution]: ...


class ProjectNeedRepository(Protocol):
    """Port for persisting and querying ProjectNeeds."""

    def find_by_id(self, need_id: str) -> ProjectNeed | None: ...

    def find_by_project_id(self, project_id: str) -> list[ProjectNeed]: ...

    def find_all_open(self) -> list[ProjectNeed]: ...

    def save(self, need: ProjectNeed) -> None: ...


class UnitOfWork(Protocol):
    """Driven port: coordinates atomic persistence of domain changes.

    Application Services manage the UoW lifecycle (enter, commit/rollback, exit).
    The domain layer defines this contract; infrastructure provides the real
    implementation (e.g., SQLAlchemy session). Tests use a FakeUnitOfWork.

    Usage::

        with uow:
            project = uow.projects.find_by_id("p1")
            project.publish()
            uow.projects.save(project)
            uow.commit()
    """

    projects: ProjectRepository
    feature_requests: FeatureRequestRepository
    products: ProductRepository
    fund: FundRepository
    needs: ProjectNeedRepository

    def __enter__(self) -> "UnitOfWork": ...
    def __exit__(self, *args: object) -> None: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...
