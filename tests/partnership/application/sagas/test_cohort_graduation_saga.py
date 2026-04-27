"""Tests for CohortGraduationSaga (Stage 15).

The saga listens to ``CohortGraduated`` and triggers
``CalculateCurationCommissionUseCase`` for every ModuleCurator in the
graduated cohort's module.  Logic is identical to CohortGraduatedHandler
but lives in the canonical ``sagas/`` package.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from cohort_learning.domain.events import CohortGraduated
from cohort_learning.domain.learning_cohort import LearningCohort
from cohort_learning.domain.peer_review import PeerReview
from cohort_learning.domain.practice_task import PracticeTask
from cohort_learning.domain.review_score import ReviewScore
from partnership.application.calculate_curation_commission import (
    CalculateCurationCommissionUseCase,
)
from partnership.application.sagas.cohort_graduation_saga import CohortGraduationSaga
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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_cohort(
    cohort_id: str = "cohort-1",
    module_id: str = "module-1",
    member_count: int = 6,
) -> LearningCohort:
    cohort = LearningCohort(
        cohort_id=cohort_id, master_id="master-1", module_id=module_id
    )
    for i in range(member_count):
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


def _make_saga(
    cohort_uow: CohortFakeUoW,
    partnership_uow: PartnershipFakeUoW,
) -> CohortGraduationSaga:
    calculate_uc = CalculateCurationCommissionUseCase(partnership_uow)
    return CohortGraduationSaga(
        cohort_uow=cohort_uow,
        calculate_commission_use_case=calculate_uc,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestCohortGraduationSaga:
    def test_creates_one_commission_per_curator(self) -> None:
        cohort_uow = CohortFakeUoW()
        partnership_uow = PartnershipFakeUoW()

        cohort = _make_cohort()
        cohort_uow.cohorts._storage["cohort-1"] = cohort

        for i in range(1, 3):
            curator = create_module_curator(
                curator_id=f"cur-{i}",
                learner_id=f"learner-{i}",
                module_id="module-1",
                cohort_id="cohort-1",
                promoted_by="master-1",
            )
            cohort_uow.module_curators._storage[f"cur-{i}"] = curator

        saga = _make_saga(cohort_uow, partnership_uow)
        saga.handle(CohortGraduated(cohort_id="cohort-1"))

        commissions = partnership_uow.commissions.find_by_cohort("cohort-1")
        assert len(commissions) == 2

    def test_no_commissions_when_no_curators(self) -> None:
        cohort_uow = CohortFakeUoW()
        partnership_uow = PartnershipFakeUoW()

        cohort_uow.cohorts._storage["cohort-1"] = _make_cohort()

        saga = _make_saga(cohort_uow, partnership_uow)
        saga.handle(CohortGraduated(cohort_id="cohort-1"))

        assert partnership_uow.commissions.find_by_cohort("cohort-1") == []

    def test_does_nothing_when_cohort_not_found(self) -> None:
        cohort_uow = CohortFakeUoW()
        partnership_uow = PartnershipFakeUoW()

        saga = _make_saga(cohort_uow, partnership_uow)
        saga.handle(CohortGraduated(cohort_id="ghost"))

        assert partnership_uow.commissions.find_by_cohort("ghost") == []

    def test_base_amount_uses_curator_score_from_helper_metrics(self) -> None:
        cohort_uow = CohortFakeUoW()
        partnership_uow = PartnershipFakeUoW()

        cohort = _make_cohort()  # 6 members
        cohort_uow.cohorts._storage["cohort-1"] = cohort

        # curator_score = 2*3 + 3*2 = 12
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

        saga = _make_saga(cohort_uow, partnership_uow)
        saga.handle(CohortGraduated(cohort_id="cohort-1"))

        commissions = partnership_uow.commissions.find_by_curator("learner-1")
        assert len(commissions) == 1
        # base_amount = 0.10 * 6 * 12 = 7.20
        assert commissions[0].base_amount == Decimal("7.20")

    def test_quality_bonus_when_avg_review_score_above_threshold(self) -> None:
        cohort_uow = CohortFakeUoW()
        partnership_uow = PartnershipFakeUoW()

        cohort = _make_cohort()
        cohort_uow.cohorts._storage["cohort-1"] = cohort

        task = PracticeTask(
            task_id="task-1",
            cohort_id="cohort-1",
            topic_id="t1",
            creator_id="master-1",
            title="T1",
        )
        task.activate()
        task.add_submission(submission_id="sub-1", learner_id="learner-0", content="s")
        task.collect_events()
        cohort_uow.practice_tasks._storage["task-1"] = task

        review = _make_review_with_scores("rev-1", "sub-1", "cohort-1", [5, 5, 5])
        cohort_uow.peer_reviews._storage["rev-1"] = review

        metrics = create_helper_metrics(
            learner_id="learner-1",
            cohort_id="cohort-1",
            tasks_reviewed=3,
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

        saga = _make_saga(cohort_uow, partnership_uow)
        saga.handle(CohortGraduated(cohort_id="cohort-1"))

        commissions = partnership_uow.commissions.find_by_curator("learner-1")
        assert commissions[0].bonus_amount > Decimal("0.00")

    def test_no_quality_bonus_when_no_reviews(self) -> None:
        cohort_uow = CohortFakeUoW()
        partnership_uow = PartnershipFakeUoW()

        cohort_uow.cohorts._storage["cohort-1"] = _make_cohort()
        curator = create_module_curator(
            curator_id="cur-1",
            learner_id="learner-1",
            module_id="module-1",
            cohort_id="cohort-1",
            promoted_by="master-1",
        )
        cohort_uow.module_curators._storage["cur-1"] = curator

        saga = _make_saga(cohort_uow, partnership_uow)
        saga.handle(CohortGraduated(cohort_id="cohort-1"))

        commissions = partnership_uow.commissions.find_by_curator("learner-1")
        assert commissions[0].bonus_amount == Decimal("0.00")
