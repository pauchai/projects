"""Repository ports and Unit of Work (driven ports) for the Partnership domain."""

from __future__ import annotations

from typing import Protocol

from partnership.domain.commission import Commission


class CommissionRepository(Protocol):
    """Port for persisting and querying Commissions."""

    def find_by_id(self, commission_id: str) -> Commission | None: ...

    def save(self, commission: Commission) -> None: ...

    def find_by_curator(self, curator_id: str) -> list[Commission]: ...

    def find_by_cohort(self, cohort_id: str) -> list[Commission]: ...


class UnitOfWork(Protocol):
    """Driven port: coordinates atomic persistence of Partnership domain changes.

    Usage::

        with uow:
            commission = uow.commissions.find_by_id("c1")
            commission.release(now=datetime.now(tz=timezone.utc))
            uow.commissions.save(commission)
            uow.commit()
    """

    commissions: CommissionRepository

    def __enter__(self) -> "UnitOfWork": ...
    def __exit__(self, *args: object) -> None: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...
