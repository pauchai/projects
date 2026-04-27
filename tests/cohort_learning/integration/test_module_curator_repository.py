"""Integration tests for SqlAlchemyModuleCuratorRepository.

Tests verify that ModuleCurator entities can be saved to and loaded from
a real PostgreSQL database through the SQLAlchemy repository.
"""

from datetime import datetime, timezone

import pytest

from cohort_learning.domain.module_curator import ModuleCurator
from cohort_learning.infrastructure.sqlalchemy_repository import (
    SqlAlchemyModuleCuratorRepository,
)


@pytest.fixture
def repo(integration_session):
    """Provide a ModuleCurator repository backed by a real database session."""
    return SqlAlchemyModuleCuratorRepository(integration_session)


class TestSqlAlchemyModuleCuratorRepository:
    """Integration tests for ModuleCurator persistence."""

    def test_save_and_find_by_id_round_trip(self, repo):
        """Saving and retrieving a ModuleCurator by ID preserves all fields."""
        # Arrange
        curator = ModuleCurator(
            curator_id="cur-1",
            learner_id="learner-1",
            module_id="module-1",
            cohort_id="cohort-1",
            promoted_at=datetime(2026, 4, 15, 12, 0, 0, tzinfo=timezone.utc),
            promoted_by="master-1",
        )

        # Act
        repo.save(curator)
        found = repo.find_by_id("cur-1")

        # Assert
        assert found is not None
        assert found.curator_id == "cur-1"
        assert found.learner_id == "learner-1"
        assert found.module_id == "module-1"
        assert found.cohort_id == "cohort-1"
        assert found.promoted_at == datetime(2026, 4, 15, 12, 0, 0, tzinfo=timezone.utc)
        assert found.promoted_by == "master-1"

    def test_find_by_id_returns_none_when_not_found(self, repo):
        """Finding a non-existent ModuleCurator returns None."""
        # Act
        found = repo.find_by_id("nonexistent")

        # Assert
        assert found is None

    def test_find_by_learner_and_module(self, repo):
        """Can find ModuleCurator by learner, module, and cohort."""
        # Arrange
        curator = ModuleCurator(
            curator_id="cur-2",
            learner_id="learner-2",
            module_id="module-2",
            cohort_id="cohort-2",
            promoted_at=datetime(2026, 4, 15, 12, 0, 0, tzinfo=timezone.utc),
            promoted_by="master-2",
        )
        repo.save(curator)

        # Act
        found = repo.find_by_learner_and_module("learner-2", "module-2", "cohort-2")

        # Assert
        assert found is not None
        assert found.curator_id == "cur-2"

    def test_find_by_learner_and_module_returns_none_when_not_found(self, repo):
        """Finding non-existent combination returns None."""
        # Act
        found = repo.find_by_learner_and_module("learner-99", "module-99", "cohort-99")

        # Assert
        assert found is None

    def test_find_by_cohort(self, repo):
        """Can find all ModuleCurators in a cohort."""
        # Arrange
        curator1 = ModuleCurator(
            curator_id="cur-3",
            learner_id="learner-3",
            module_id="module-1",
            cohort_id="cohort-3",
            promoted_at=datetime(2026, 4, 15, 12, 0, 0, tzinfo=timezone.utc),
            promoted_by="master-3",
        )
        curator2 = ModuleCurator(
            curator_id="cur-4",
            learner_id="learner-4",
            module_id="module-2",
            cohort_id="cohort-3",
            promoted_at=datetime(2026, 4, 15, 13, 0, 0, tzinfo=timezone.utc),
            promoted_by="master-3",
        )
        curator3 = ModuleCurator(
            curator_id="cur-5",
            learner_id="learner-5",
            module_id="module-3",
            cohort_id="cohort-999",  # different cohort
            promoted_at=datetime(2026, 4, 15, 14, 0, 0, tzinfo=timezone.utc),
            promoted_by="master-3",
        )
        repo.save(curator1)
        repo.save(curator2)
        repo.save(curator3)

        # Act
        curators = repo.find_by_cohort("cohort-3")

        # Assert
        assert len(curators) == 2
        curator_ids = {c.curator_id for c in curators}
        assert curator_ids == {"cur-3", "cur-4"}
