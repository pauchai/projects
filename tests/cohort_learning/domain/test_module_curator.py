"""Tests for ModuleCurator entity."""

import pytest
from datetime import datetime, UTC

from cohort_learning.domain.module_curator import ModuleCurator


class TestModuleCuratorCreation:
    def test_create_module_curator_with_valid_data(self) -> None:
        # Arrange & Act
        curator = ModuleCurator(
            curator_id="cur-1",
            learner_id="learner-1",
            module_id="module-frontend-basics",
            cohort_id="cohort-1",
            promoted_at=datetime(2026, 4, 15, 10, 0, 0, tzinfo=UTC),
            promoted_by="master-1",
        )

        # Assert
        assert curator.curator_id == "cur-1"
        assert curator.learner_id == "learner-1"
        assert curator.module_id == "module-frontend-basics"
        assert curator.cohort_id == "cohort-1"
        assert curator.promoted_at == datetime(2026, 4, 15, 10, 0, 0, tzinfo=UTC)
        assert curator.promoted_by == "master-1"

    def test_module_curator_attributes_are_accessible(self) -> None:
        # Arrange
        curator = ModuleCurator(
            curator_id="cur-1",
            learner_id="learner-1",
            module_id="module-frontend-basics",
            cohort_id="cohort-1",
            promoted_at=datetime(2026, 4, 15, 10, 0, 0, tzinfo=UTC),
            promoted_by="master-1",
        )

        # Act & Assert — curator status is permanent (business rule, not enforced by immutability)
        assert curator.module_id == "module-frontend-basics"
        assert curator.learner_id == "learner-1"


class TestModuleCuratorEquality:
    def test_curators_equal_by_curator_id(self) -> None:
        # Arrange
        curator1 = ModuleCurator(
            curator_id="cur-1",
            learner_id="learner-1",
            module_id="module-frontend-basics",
            cohort_id="cohort-1",
            promoted_at=datetime(2026, 4, 15, 10, 0, 0, tzinfo=UTC),
            promoted_by="master-1",
        )
        curator2 = ModuleCurator(
            curator_id="cur-1",
            learner_id="learner-999",  # different learner
            module_id="module-other",  # different module
            cohort_id="cohort-999",
            promoted_at=datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC),
            promoted_by="other",
        )

        # Act & Assert — identity by curator_id
        assert curator1 == curator2

    def test_different_curator_ids_not_equal(self) -> None:
        # Arrange
        curator1 = ModuleCurator(
            curator_id="cur-1",
            learner_id="learner-1",
            module_id="module-frontend-basics",
            cohort_id="cohort-1",
            promoted_at=datetime(2026, 4, 15, 10, 0, 0, tzinfo=UTC),
            promoted_by="master-1",
        )
        curator2 = ModuleCurator(
            curator_id="cur-2",
            learner_id="learner-1",  # same learner
            module_id="module-frontend-basics",  # same module
            cohort_id="cohort-1",
            promoted_at=datetime(2026, 4, 15, 10, 0, 0, tzinfo=UTC),
            promoted_by="master-1",
        )

        # Act & Assert
        assert curator1 != curator2


class TestModuleCuratorBusinessRules:
    def test_curator_status_is_module_specific(self) -> None:
        # Arrange — same learner can be curator in multiple modules
        curator_frontend = ModuleCurator(
            curator_id="cur-1",
            learner_id="learner-1",
            module_id="module-frontend-basics",
            cohort_id="cohort-1",
            promoted_at=datetime(2026, 4, 15, 10, 0, 0, tzinfo=UTC),
            promoted_by="master-1",
        )
        curator_backend = ModuleCurator(
            curator_id="cur-2",
            learner_id="learner-1",  # same learner
            module_id="module-backend-architecture",  # different module
            cohort_id="cohort-2",
            promoted_at=datetime(2026, 5, 15, 10, 0, 0, tzinfo=UTC),
            promoted_by="master-2",
        )

        # Act & Assert — curator in frontend ≠ curator in backend
        assert curator_frontend.learner_id == curator_backend.learner_id
        assert curator_frontend.module_id != curator_backend.module_id
        assert curator_frontend != curator_backend

    def test_cohort_id_indicates_where_status_was_earned(self) -> None:
        # Arrange
        curator = ModuleCurator(
            curator_id="cur-1",
            learner_id="learner-1",
            module_id="module-frontend-basics",
            cohort_id="cohort-1",  # earned in cohort 1
            promoted_at=datetime(2026, 4, 15, 10, 0, 0, tzinfo=UTC),
            promoted_by="master-1",
        )

        # Act & Assert — cohort_id tracks historical context
        # Curator can lead future cohorts of same module (validated by application layer)
        assert curator.cohort_id == "cohort-1"
