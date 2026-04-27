"""CohortGraduationSaga — Stage 15.

Listens to ``CohortGraduated`` and triggers commission calculation for every
``ModuleCurator`` in the graduated cohort's module.

This saga is the canonical entry point for commission generation on graduation.
It reads cohort data (module, curators, helper metrics, avg review score) from
the cohort_learning UoW (read-only) and delegates all Partnership writes to
``CalculateCurationCommissionUseCase``.
"""

from __future__ import annotations

from cohort_learning.domain.events import CohortGraduated
from cohort_learning.domain.ports import UnitOfWork as CohortUnitOfWork
from partnership.application.calculate_curation_commission import (
    CalculateCurationCommissionUseCase,
)
from shared_kernel.events import DomainEvent


class CohortGraduationSaga:
    """Saga: calculate curation commissions when a cohort graduates.

    Constructor args:
        cohort_uow: CohortUnitOfWork — read-only access to cohort domain data.
        calculate_commission_use_case: CalculateCurationCommissionUseCase —
            handles the actual commission creation in the partnership context.
    """

    def __init__(
        self,
        cohort_uow: CohortUnitOfWork,
        calculate_commission_use_case: CalculateCurationCommissionUseCase,
    ) -> None:
        self._cohort_uow = cohort_uow
        self._calculate_commission_uc = calculate_commission_use_case

    def handle(self, event: DomainEvent) -> None:
        assert isinstance(event, CohortGraduated)
        self._process(event)

    # -------------------------------------------------------------------------
    # Internal processing
    # -------------------------------------------------------------------------

    def _process(self, event: CohortGraduated) -> None:
        with self._cohort_uow as uow:
            cohort = uow.cohorts.find_by_id(event.cohort_id)
            if cohort is None:
                return

            cohort_size = len(cohort.memberships)
            curators = uow.module_curators.find_by_module(cohort.module_id)
            avg_review_score = self._compute_avg_review_score(uow, event.cohort_id)

            for curator in curators:
                curator_score = self._compute_curator_score(
                    uow, curator.learner_id, event.cohort_id
                )
                self._calculate_commission_uc.execute(
                    curator_id=curator.learner_id,
                    cohort_id=event.cohort_id,
                    module_id=cohort.module_id,
                    cohort_size=cohort_size,
                    curator_score=curator_score,
                    avg_review_score=avg_review_score,
                )

    # -------------------------------------------------------------------------
    # Private helpers
    # -------------------------------------------------------------------------

    def _compute_curator_score(
        self, uow: CohortUnitOfWork, learner_id: str, cohort_id: str
    ) -> int:
        """Compute curator_score = tasks_reviewed * 3 + learners_helped * 2."""
        metrics = uow.helper_metrics.find_by_learner_and_cohort(learner_id, cohort_id)
        if metrics is None:
            return 0
        return metrics.tasks_reviewed * 3 + metrics.learners_helped * 2

    def _compute_avg_review_score(self, uow: CohortUnitOfWork, cohort_id: str) -> float:
        """Compute average peer review score across all reviews in the cohort.

        Iterates tasks → submissions → reviews → scores.
        Returns 0.0 if no reviews exist.
        """
        tasks = uow.practice_tasks.find_by_cohort(cohort_id)
        all_review_averages: list[float] = []

        for task in tasks:
            for submission in task.submissions:
                reviews = uow.peer_reviews.find_by_submission(submission.submission_id)
                for review in reviews:
                    if review.scores:
                        review_avg = sum(s.score for s in review.scores) / len(
                            review.scores
                        )
                        all_review_averages.append(review_avg)

        if not all_review_averages:
            return 0.0
        return sum(all_review_averages) / len(all_review_averages)
