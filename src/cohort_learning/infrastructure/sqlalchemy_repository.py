"""SQLAlchemy ORM-based repository adapter (driven adapter) for LearningCohort.

Uses SQLAlchemy ORM with Imperative Mapping (configured in ``orm.py``).
Domain classes are loaded/saved as mapped objects; the ORM handles
``__new__`` + attribute population on load, bypassing ``__init__``.

``_events`` is NOT persisted — it is a transient list of domain events,
initialised after load via ``_init_transient()``.
"""

from __future__ import annotations

from sqlalchemy.orm import Session, selectinload

from cohort_learning.domain.learning_cohort import LearningCohort


class SqlAlchemyCohortRepository:
    """Implements CohortRepository Protocol using SQLAlchemy ORM."""

    def __init__(self, session: Session, uow: object | None = None) -> None:
        self._session = session
        self._uow = uow

    # ------------------------------------------------------------------
    # Public interface (matches CohortRepository Protocol)
    # ------------------------------------------------------------------

    def find_by_id(self, cohort_id: str) -> LearningCohort | None:
        """Load a full LearningCohort aggregate by ID, or return None."""
        cohort = self._session.get(
            LearningCohort,
            cohort_id,
            options=[
                selectinload(LearningCohort.memberships),  # type: ignore[attr-defined]
            ],
        )
        if cohort is None:
            return None

        self._init_transient(cohort)
        return cohort

    def save(self, cohort: LearningCohort) -> None:
        """Persist a LearningCohort aggregate (cohort + memberships).

        Collects domain events from the aggregate and passes them to the UoW
        for publishing after commit.
        """
        # 1. Collect domain events before merge (merge may return a different object)
        events = cohort.collect_events()
        if events and self._uow is not None and hasattr(self._uow, "collect_events"):
            self._uow.collect_events(events)

        # 2. Merge the aggregate (cohort + relationships handled by ORM)
        self._session.merge(cohort)
        # Flush to ensure the cohort row exists
        self._session.flush()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _init_transient(cohort: LearningCohort) -> None:
        """Initialise transient attributes that the ORM does not populate."""
        if not hasattr(cohort, "_events"):
            cohort._events = []
