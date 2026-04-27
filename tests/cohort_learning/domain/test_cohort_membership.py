"""Tests for CohortMembership entity."""

import pytest

from cohort_learning.domain.cohort_role import CohortRole


class TestCohortMembershipCreation:
    """CohortMembership is created with default Learner role."""

    def test_creates_with_learner_role(self) -> None:
        from cohort_learning.domain.cohort_membership import CohortMembership

        membership = CohortMembership(
            membership_id="mem1",
            learner_id="u1",
            cohort_id="c1",
        )
        assert membership.role == CohortRole.LEARNER

    def test_stores_membership_id(self) -> None:
        from cohort_learning.domain.cohort_membership import CohortMembership

        membership = CohortMembership(
            membership_id="mem1",
            learner_id="u1",
            cohort_id="c1",
        )
        assert membership.membership_id == "mem1"

    def test_stores_learner_id(self) -> None:
        from cohort_learning.domain.cohort_membership import CohortMembership

        membership = CohortMembership(
            membership_id="mem1",
            learner_id="u1",
            cohort_id="c1",
        )
        assert membership.learner_id == "u1"

    def test_stores_cohort_id(self) -> None:
        from cohort_learning.domain.cohort_membership import CohortMembership

        membership = CohortMembership(
            membership_id="mem1",
            learner_id="u1",
            cohort_id="c1",
        )
        assert membership.cohort_id == "c1"

    def test_is_active_by_default(self) -> None:
        from cohort_learning.domain.cohort_membership import CohortMembership

        membership = CohortMembership(
            membership_id="mem1",
            learner_id="u1",
            cohort_id="c1",
        )
        assert membership.is_active is True

    def test_has_joined_at_timestamp(self) -> None:
        from cohort_learning.domain.cohort_membership import CohortMembership

        membership = CohortMembership(
            membership_id="mem1",
            learner_id="u1",
            cohort_id="c1",
        )
        assert membership.joined_at is not None


class TestCohortMembershipDeactivation:
    """Deactivation marks the membership as inactive."""

    def test_deactivate_sets_inactive(self) -> None:
        from cohort_learning.domain.cohort_membership import CohortMembership

        membership = CohortMembership(
            membership_id="mem1",
            learner_id="u1",
            cohort_id="c1",
        )
        membership.deactivate()
        assert membership.is_active is False

    def test_deactivate_raises_when_already_inactive(self) -> None:
        from cohort_learning.domain.cohort_membership import CohortMembership

        membership = CohortMembership(
            membership_id="mem1",
            learner_id="u1",
            cohort_id="c1",
        )
        membership.deactivate()
        with pytest.raises(ValueError, match="already inactive"):
            membership.deactivate()


class TestCohortMembershipRolePromotion:
    """Role promotion follows the progression order."""

    def test_promote_to_topic_expert(self) -> None:
        from cohort_learning.domain.cohort_membership import CohortMembership

        membership = CohortMembership(
            membership_id="mem1",
            learner_id="u1",
            cohort_id="c1",
        )
        membership.promote_to(CohortRole.TOPIC_EXPERT)
        assert membership.role == CohortRole.TOPIC_EXPERT

    def test_promote_to_module_curator(self) -> None:
        from cohort_learning.domain.cohort_membership import CohortMembership

        membership = CohortMembership(
            membership_id="mem1",
            learner_id="u1",
            cohort_id="c1",
        )
        membership.promote_to(CohortRole.TOPIC_EXPERT)
        membership.promote_to(CohortRole.MODULE_CURATOR)
        assert membership.role == CohortRole.MODULE_CURATOR

    def test_cannot_promote_to_lower_role(self) -> None:
        from cohort_learning.domain.cohort_membership import CohortMembership

        membership = CohortMembership(
            membership_id="mem1",
            learner_id="u1",
            cohort_id="c1",
        )
        membership.promote_to(CohortRole.TOPIC_EXPERT)
        with pytest.raises(ValueError, match="Cannot demote"):
            membership.promote_to(CohortRole.LEARNER)

    def test_cannot_promote_to_same_role(self) -> None:
        from cohort_learning.domain.cohort_membership import CohortMembership

        membership = CohortMembership(
            membership_id="mem1",
            learner_id="u1",
            cohort_id="c1",
        )
        with pytest.raises(ValueError, match="Cannot demote"):
            membership.promote_to(CohortRole.LEARNER)

    def test_cannot_promote_to_master(self) -> None:
        from cohort_learning.domain.cohort_membership import CohortMembership

        membership = CohortMembership(
            membership_id="mem1",
            learner_id="u1",
            cohort_id="c1",
        )
        with pytest.raises(ValueError, match="Cannot promote.*Master"):
            membership.promote_to(CohortRole.MASTER)

    def test_cannot_promote_inactive_membership(self) -> None:
        from cohort_learning.domain.cohort_membership import CohortMembership

        membership = CohortMembership(
            membership_id="mem1",
            learner_id="u1",
            cohort_id="c1",
        )
        membership.deactivate()
        with pytest.raises(ValueError, match="inactive membership"):
            membership.promote_to(CohortRole.TOPIC_EXPERT)
