"""Tests for CohortRole enum and privilege hierarchy."""


class TestCohortRoleValues:
    """CohortRole enum should have exactly 4 values."""

    def test_has_learner_role(self) -> None:
        from cohort_learning.domain.cohort_role import CohortRole

        assert CohortRole.LEARNER.value == "learner"

    def test_has_topic_expert_role(self) -> None:
        from cohort_learning.domain.cohort_role import CohortRole

        assert CohortRole.TOPIC_EXPERT.value == "topic_expert"

    def test_has_module_curator_role(self) -> None:
        from cohort_learning.domain.cohort_role import CohortRole

        assert CohortRole.MODULE_CURATOR.value == "module_curator"

    def test_has_master_role(self) -> None:
        from cohort_learning.domain.cohort_role import CohortRole

        assert CohortRole.MASTER.value == "master"

    def test_has_exactly_four_values(self) -> None:
        from cohort_learning.domain.cohort_role import CohortRole

        assert len(CohortRole) == 4


class TestCohortRoleTeachingRights:
    """Only Topic Expert, Module Curator, and Master can teach/review."""

    def test_learner_cannot_teach(self) -> None:
        from cohort_learning.domain.cohort_role import CohortRole

        assert CohortRole.LEARNER.can_review_tasks() is False

    def test_topic_expert_can_review_tasks(self) -> None:
        from cohort_learning.domain.cohort_role import CohortRole

        assert CohortRole.TOPIC_EXPERT.can_review_tasks() is True

    def test_module_curator_can_review_tasks(self) -> None:
        from cohort_learning.domain.cohort_role import CohortRole

        assert CohortRole.MODULE_CURATOR.can_review_tasks() is True

    def test_master_can_review_tasks(self) -> None:
        from cohort_learning.domain.cohort_role import CohortRole

        assert CohortRole.MASTER.can_review_tasks() is True


class TestCohortRoleCurationRights:
    """Only Module Curator and Master can curate cohorts."""

    def test_learner_cannot_curate(self) -> None:
        from cohort_learning.domain.cohort_role import CohortRole

        assert CohortRole.LEARNER.can_curate() is False

    def test_topic_expert_cannot_curate(self) -> None:
        from cohort_learning.domain.cohort_role import CohortRole

        assert CohortRole.TOPIC_EXPERT.can_curate() is False

    def test_module_curator_can_curate(self) -> None:
        from cohort_learning.domain.cohort_role import CohortRole

        assert CohortRole.MODULE_CURATOR.can_curate() is True

    def test_master_can_curate(self) -> None:
        from cohort_learning.domain.cohort_role import CohortRole

        assert CohortRole.MASTER.can_curate() is True


class TestCohortRoleProgression:
    """Progression order: Learner < Topic Expert < Module Curator < Master."""

    def test_learner_is_below_topic_expert(self) -> None:
        from cohort_learning.domain.cohort_role import CohortRole

        assert CohortRole.LEARNER.rank < CohortRole.TOPIC_EXPERT.rank

    def test_topic_expert_is_below_module_curator(self) -> None:
        from cohort_learning.domain.cohort_role import CohortRole

        assert CohortRole.TOPIC_EXPERT.rank < CohortRole.MODULE_CURATOR.rank

    def test_module_curator_is_below_master(self) -> None:
        from cohort_learning.domain.cohort_role import CohortRole

        assert CohortRole.MODULE_CURATOR.rank < CohortRole.MASTER.rank
