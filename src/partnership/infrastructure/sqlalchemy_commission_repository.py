"""SQLAlchemy ORM-based Commission repository (driven adapter) for Partnership.

Uses SQLAlchemy ORM with Imperative Mapping (configured in ``orm.py``).
``_events`` is NOT persisted — it is a transient list of domain events,
initialised after load via ``_init_transient()``.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from partnership.domain.commission import Commission


class SqlAlchemyCommissionRepository:
    """Implements CommissionRepository Protocol using SQLAlchemy ORM."""

    def __init__(self, session: Session, uow: object | None = None) -> None:
        self._session = session
        self._uow = uow

    # ------------------------------------------------------------------
    # Public interface (matches CommissionRepository Protocol)
    # ------------------------------------------------------------------

    def find_by_id(self, commission_id: str) -> Commission | None:
        """Load a Commission by ID, or return None."""
        commission = self._session.get(Commission, commission_id)
        if commission is None:
            return None
        self._init_transient(commission)
        return commission

    def save(self, commission: Commission) -> None:
        """Persist a Commission aggregate.

        Collects domain events from the aggregate and passes them to the UoW
        for publishing after commit.
        """
        events = commission.collect_events()
        if events and self._uow is not None and hasattr(self._uow, "collect_events"):
            self._uow.collect_events(events)

        self._session.merge(commission)
        self._session.flush()

    def find_by_curator(self, curator_id: str) -> list[Commission]:
        """Return all Commissions belonging to a curator."""
        stmt = select(Commission).where(
            Commission.curator_id == curator_id  # type: ignore[attr-defined]
        )
        commissions = list(self._session.scalars(stmt).all())
        for c in commissions:
            self._init_transient(c)
        return commissions

    def find_by_cohort(self, cohort_id: str) -> list[Commission]:
        """Return all Commissions for a given cohort."""
        stmt = select(Commission).where(
            Commission.cohort_id == cohort_id  # type: ignore[attr-defined]
        )
        commissions = list(self._session.scalars(stmt).all())
        for c in commissions:
            self._init_transient(c)
        return commissions

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _init_transient(commission: Commission) -> None:
        """Initialise transient attributes that the ORM does not populate."""
        if not hasattr(commission, "_events"):
            commission._events = []
