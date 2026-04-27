"""Tests for CohortGraduatedHandler (ACL) — Stage 11 RED phase."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from cohort_learning.domain.cohort_membership import CohortMembership
from cohort_learning.domain.events import CohortGraduated
from cohort_learning.domain.learning_cohort import LearningCohort
from cohort_learning.domain.peer_review import PeerReview
from cohort_learning.domain.practice_task import PracticeTask
from cohort_learning.domain.review_score import ReviewScore
from partnership.application.calculate_curation_commission import (
    CalculateCurationCommissionUseCase,
)
from partnership.application.event_handlers.cohort_graduated_handler import (
    CohortGraduatedHandler,
)
from tests.cohort_learning.factories import (
    create_helper_metrics,
    create_module_curator,
)
from tests.cohort_learning.fakes.fake_unit_of_work import (
    FakeUnitOfWork as CohortFakeUoW,
)
from tests.partnership.fakes.fake_unit_of_work import (
    FakeUnitOfWork as PartnershipFakeUoW,
)

_NOW = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_cohort(
    cohort_id: str = "cohort-1", module_id: str = "module-1"
) -> LearningCohort:
    cohort = LearningCohort(
        cohort_id=cohort_id, master_id="master-1", module_id=module_id
    )
    # Enrol 6 learners so cohort can be activated
    for i in range(6):
        cohort.enrol_learner(membership_id=f"mem-{i}", learner_id=f"learner-{i}")
    cohort.collect_events()
    return cohort


def _make_review_with_scores(
    review_id: str,
    submission_id: str,
    cohort_id: str,
    scores: list[int],
) -> PeerReview:
    review = PeerReview(
        review_id=review_id,
        submission_id=submission_id,
        reviewer_id="learner-0",
        task_id="task-1",
        cohort_id=cohort_id,
    )
    for i, score in enumerate(scores):
        review.scores.append(ReviewScore(criterion=f"c{i}", score=score))
    return review


def _make_handler(
    cohort_uow: CohortFakeUoW,
    partnership_uow: PartnershipFakeUoW,
) -> CohortGraduatedHandler:
    calculate_uc = CalculateCurationCommissionUseCase(partnership_uow)
    return CohortGraduatedHandler(
        cohort_uow=cohort_uow,
        calculate_commission_use_case=calculate_uc,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestCohortGraduatedHandler:
    def test_creates_one_commission_per_curator(self) -> None:
        cohort_uow = CohortFakeUoW()
        partnership_uow = PartnershipFakeUoW()

        cohort = _make_cohort()
        cohort_uow.cohorts._storage["cohort-1"] = cohort

        curator1 = create_module_curator(
            curator_id="cur-1",
            learner_id="learner-1",
            module_id="module-1",
            cohort_id="cohort-1",
            promoted_by="master-1",
        )
        curator2 = create_module_curator(
            curator_id="cur-2",
            learner_id="learner-2",
            module_id="module-1",
            cohort_id="cohort-1",
            promoted_by="master-1",
        )
        cohort_uow.module_curators._storage["cur-1"] = curator1
        cohort_uow.module_curators._storage["cur-2"] = curator2

        handler = _make_handler(cohort_uow, partnership_uow)
        handler.handle(CohortGraduated(cohort_id="cohort-1"))

        commissions = partnership_uow.commissions.find_by_cohort("cohort-1")
        assert len(commissions) == 2

    def test_commission_curator_ids_match_module_curators(self) -> None:
        cohort_uow = CohortFakeUoW()
        partnership_uow = PartnershipFakeUoW()

        cohort = _make_cohort()
        cohort_uow.cohorts._storage["cohort-1"] = cohort

        curator = create_module_curator(
            curator_id="cur-1",
            learner_id="learner-5",
            module_id="module-1",
            cohort_id="cohort-1",
            promoted_by="master-1",
        )
        cohort_uow.module_curators._storage["cur-1"] = curator

        handler = _make_handler(cohort_uow, partnership_uow)
        handler.handle(CohortGraduated(cohort_id="cohort-1"))

        commissions = partnership_uow.commissions.find_by_curator("learner-5")
        assert len(commissions) == 1

    def test_no_commissions_when_no_curators(self) -> None:
        cohort_uow = CohortFakeUoW()
        partnership_uow = PartnershipFakeUoW()

        cohort = _make_cohort()
        cohort_uow.cohorts._storage["cohort-1"] = cohort

        handler = _make_handler(cohort_uow, partnership_uow)
        handler.handle(CohortGraduated(cohort_id="cohort-1"))

        commissions = partnership_uow.commissions.find_by_cohort("cohort-1")
        assert commissions == []

    def test_no_error_when_cohort_not_found(self) -> None:
        cohort_uow = CohortFakeUoW()
        partnership_uow = PartnershipFakeUoW()

        handler = _make_handler(cohort_uow, partnership_uow)
        # Should not raise
        handler.handle(CohortGraduated(cohort_id="nonexistent"))

        commissions = partnership_uow.commissions.find_by_cohort("nonexistent")
        assert commissions == []

    def test_base_amount_uses_cohort_size_from_memberships(self) -> None:
        cohort_uow = CohortFakeUoW()
        partnership_uow = PartnershipFakeUoW()

        cohort = _make_cohort()  # 6 members
        cohort_uow.cohorts._storage["cohort-1"] = cohort

        # curator_score = tasks_reviewed*3 + learners_helped*2 = 2*3 + 3*2 = 12
        metrics = create_helper_metrics(
            learner_id="learner-1",
            cohort_id="cohort-1",
            tasks_reviewed=2,
            learners_helped=3,
        )
        cohort_uow.helper_metrics._storage[("learner-1", "cohort-1")] = metrics

        curator = create_module_curator(
            curator_id="cur-1",
            learner_id="learner-1",
            module_id="module-1",
            cohort_id="cohort-1",
            promoted_by="master-1",
        )
        cohort_uow.module_curators._storage["cur-1"] = curator

        handler = _make_handler(cohort_uow, partnership_uow)
        handler.handle(CohortGraduated(cohort_id="cohort-1"))

        commissions = partnership_uow.commissions.find_by_curator("learner-1")
        assert len(commissions) == 1
        # base_amount = 0.10 * 6 (cohort_size) * 12 (curator_score) = 7.20
        assert commissions[0].base_amount == Decimal("7.20")

    def test_curator_score_zero_when_no_helper_metrics(self) -> None:
        cohort_uow = CohortFakeUoW()
        partnership_uow = PartnershipFakeUoW()

        cohort = _make_cohort()
        cohort_uow.cohorts._storage["cohort-1"] = cohort

        curator = create_module_curator(
            curator_id="cur-1",
            learner_id="learner-1",
            module_id="module-1",
            cohort_id="cohort-1",
            promoted_by="master-1",
        )
        cohort_uow.module_curators._storage["cur-1"] = curator
        # No helper metrics for learner-1

        handler = _make_handler(cohort_uow, partnership_uow)
        handler.handle(CohortGraduated(cohort_id="cohort-1"))

        commissions = partnership_uow.commissions.find_by_curator("learner-1")
        # base_amount = 0.10 * 6 * 0 = 0.00
        assert commissions[0].base_amount == Decimal("0.00")

    def test_quality_bonus_applied_when_avg_review_score_above_4_5(self) -> None:
        cohort_uow = CohortFakeUoW()
        partnership_uow = PartnershipFakeUoW()

        cohort = _make_cohort()
        cohort_uow.cohorts._storage["cohort-1"] = cohort

        # Set up a task with a submission that has a high-scoring review
        task = PracticeTask(
            task_id="task-1",
            cohort_id="cohort-1",
            topic_id="t1",
            creator_id="master-1",
            title="Task 1",
        )
        task.activate()
        task.add_submission(
            submission_id="sub-1", learner_id="learner-0", content="solution"
        )
        task.collect_events()
        cohort_uow.practice_tasks._storage["task-1"] = task

        review = _make_review_with_scores(
            review_id="rev-1",
            submission_id="sub-1",
            cohort_id="cohort-1",
            scores=[5, 5, 5],  # avg = 5.0 > 4.5
        )
        cohort_uow.peer_reviews._storage["rev-1"] = review

        # curator with enough score to exceed threshold
        metrics = create_helper_metrics(
            learner_id="learner-1",
            cohort_id="cohort-1",
            tasks_reviewed=5,
            learners_helped=5,
        )
        cohort_uow.helper_metrics._storage[("learner-1", "cohort-1")] = metrics
        curator = create_module_curator(
            curator_id="cur-1",
            learner_id="learner-1",
            module_id="module-1",
            cohort_id="cohort-1",
            promoted_by="master-1",
        )
        cohort_uow.module_curators._storage["cur-1"] = curator

        handler = _make_handler(cohort_uow, partnership_uow)
        handler.handle(CohortGraduated(cohort_id="cohort-1"))

        commissions = partnership_uow.commissions.find_by_curator("learner-1")
        assert len(commissions) == 1
        assert commissions[0].bonus_amount > Decimal("0.00")

    def test_no_quality_bonus_when_avg_review_score_at_or_below_4_5(self) -> None:
        cohort_uow = CohortFakeUoW()
        partnership_uow = PartnershipFakeUoW()

        cohort = _make_cohort()
        cohort_uow.cohorts._storage["cohort-1"] = cohort

        # Set up a task with a low-scoring review
        task = PracticeTask(
            task_id="task-1",
            cohort_id="cohort-1",
            topic_id="t1",
            creator_id="master-1",
            title="Task 1",
        )
        task.activate()
        task.add_submission(submission_id="sub-1", learner_id="learner-0", content="s")
        task.collect_events()
        cohort_uow.practice_tasks._storage["task-1"] = task

        review = _make_review_with_scores(
            review_id="rev-1",
            submission_id="sub-1",
            cohort_id="cohort-1",
            scores=[4, 4, 5],  # avg = 4.33 <= 4.5
        )
        cohort_uow.peer_reviews._storage["rev-1"] = review

        curator = create_module_curator(
            curator_id="cur-1",
            learner_id="learner-1",
            module_id="module-1",
            cohort_id="cohort-1",
            promoted_by="master-1",
        )
        cohort_uow.module_curators._storage["cur-1"] = curator

        handler = _make_handler(cohort_uow, partnership_uow)
        handler.handle(CohortGraduated(cohort_id="cohort-1"))

        commissions = partnership_uow.commissions.find_by_curator("learner-1")
        assert commissions[0].bonus_amount == Decimal("0.00")

    def test_avg_review_score_is_zero_when_no_reviews(self) -> None:
        """Handler should not crash and should produce no quality bonus."""
        cohort_uow = CohortFakeUoW()
        partnership_uow = PartnershipFakeUoW()

        cohort = _make_cohort()
        cohort_uow.cohorts._storage["cohort-1"] = cohort

        curator = create_module_curator(
            curator_id="cur-1",
            learner_id="learner-1",
            module_id="module-1",
            cohort_id="cohort-1",
            promoted_by="master-1",
        )
        cohort_uow.module_curators._storage["cur-1"] = curator

        handler = _make_handler(cohort_uow, partnership_uow)
        handler.handle(CohortGraduated(cohort_id="cohort-1"))

        commissions = partnership_uow.commissions.find_by_curator("learner-1")
        assert commissions[0].bonus_amount == Decimal("0.00")
