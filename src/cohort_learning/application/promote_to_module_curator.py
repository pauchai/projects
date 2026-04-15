"""PromoteToModuleCurator use case."""

from datetime import datetime, timezone

from cohort_learning.application._helpers import get_cohort_or_raise, require_master
from cohort_learning.domain.curator_promotion import CuratorPromotionService
from cohort_learning.domain.events import CuratorPromoted
from cohort_learning.domain.helper_metrics import HelperMetrics
from cohort_learning.domain.module_curator import ModuleCurator
from cohort_learning.domain.ports import UnitOfWork


class PromoteToModuleCuratorUseCase:
    """Promote a learner to Module Curator after meeting all requirements.

    Requirements (evaluated by CuratorPromotionService):
    1. Module Completion — all topics with Topic Competency
    2. Helper Track Record — HelperMetrics meets curator threshold
    3. Teaching Trial — assisted 2-3 learners successfully
    4. Master Approval — explicit confirmation

    Only Master can promote to Module Curator.
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(
        self,
        curator_id: str,
        learner_id: str,
        module_id: str,
        cohort_id: str,
        master_id: str,
        module_completed: bool,
        teaching_trial_passed: bool,
    ) -> ModuleCurator:
        with self._uow as uow:
            cohort = get_cohort_or_raise(uow, cohort_id)
            require_master(cohort, master_id)

            # Check if learner is already a Module Curator for this module
            existing_curator = uow.module_curators.find_by_learner_and_module(
                learner_id, module_id
            )
            if existing_curator is not None:
                raise ValueError(
                    f"Learner '{learner_id}' is already a Module Curator for module '{module_id}'"
                )

            # Get helper metrics
            helper_metrics = uow.helper_metrics.find_by_learner(learner_id, cohort_id)
            if helper_metrics is None:
                # No helper activity recorded — create empty metrics
                helper_metrics = HelperMetrics(
                    learner_id=learner_id,
                    cohort_id=cohort_id,
                    learners_helped=0,
                    questions_answered=0,
                    tasks_reviewed=0,
                    average_satisfaction=None,
                    updated_at=datetime.now(timezone.utc),
                )

            # Evaluate promotion using domain service
            promotion_service = CuratorPromotionService()
            result = promotion_service.evaluate_promotion(
                learner_id=learner_id,
                module_id=module_id,
                helper_metrics=helper_metrics,
                module_completed=module_completed,
                teaching_trial_passed=teaching_trial_passed,
                master_approved=True,  # Master is calling this, so approved
            )

            if not result.is_approved:
                feedback = result.get_feedback()
                raise ValueError(
                    f"Learner '{learner_id}' does not meet promotion requirements. {feedback}"
                )

            # Create ModuleCurator entity
            curator = ModuleCurator(
                curator_id=curator_id,
                learner_id=learner_id,
                module_id=module_id,
                cohort_id=cohort_id,
                promoted_at=datetime.now(timezone.utc),
                promoted_by=master_id,
            )

            # Emit domain event
            event = CuratorPromoted(
                learner_id=learner_id,
                module_id=module_id,
                cohort_id=cohort_id,
            )
            uow.collect_events([event])

            uow.module_curators.save(curator)
            uow.commit()
            return curator
