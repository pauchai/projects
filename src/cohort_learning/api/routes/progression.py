"""Partner Progression routes: REST endpoints for Topic Expert and Module Curator promotion."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from cohort_learning.api.dependencies import get_cohort_uow, get_current_user_id
from cohort_learning.api.schemas import (
    CompetencyValidationResult,
    HelperMetricsResponse,
    MessageResponse,
    ModuleCuratorResponse,
    PendingCompetencyValidationResponse,
    PendingCuratorPromotionResponse,
    PromoteToModuleCuratorRequest,
    PromoteToTopicExpertRequest,
    TopicExpertResponse,
    ValidateTopicCompetencyRequest,
)
from cohort_learning.application.get_pending_competency_validations import (
    GetPendingCompetencyValidationsUseCase,
)
from cohort_learning.application.get_pending_curator_promotions import (
    GetPendingCuratorPromotionsUseCase,
)
from cohort_learning.application.promote_to_module_curator import (
    PromoteToModuleCuratorUseCase,
)
from cohort_learning.application.promote_to_topic_expert import (
    PromoteToTopicExpertUseCase,
)
from cohort_learning.application.validate_topic_competency import (
    ValidateTopicCompetencyUseCase,
)
from cohort_learning.domain.helper_metrics import HelperMetrics
from cohort_learning.domain.module_curator import ModuleCurator
from cohort_learning.domain.topic_expert import TopicExpert
from cohort_learning.infrastructure.sqlalchemy_unit_of_work import (
    SqlAlchemyUnitOfWork,
)

router = APIRouter(prefix="/cohorts", tags=["partner-progression"])


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------


def _topic_expert_to_response(expert: TopicExpert) -> TopicExpertResponse:
    return TopicExpertResponse(
        expert_id=expert.expert_id,
        learner_id=expert.learner_id,
        topic_id=expert.topic_id,
        cohort_id=expert.cohort_id,
        validated_at=expert.validated_at,
        validator_id=expert.validator_id,
    )


def _helper_metrics_to_response(metrics: HelperMetrics) -> HelperMetricsResponse:
    return HelperMetricsResponse(
        learner_id=metrics.learner_id,
        cohort_id=metrics.cohort_id,
        learners_helped=metrics.learners_helped,
        questions_answered=metrics.questions_answered,
        tasks_reviewed=metrics.tasks_reviewed,
        average_satisfaction=metrics.average_satisfaction,
        updated_at=metrics.updated_at,
    )


def _module_curator_to_response(curator: ModuleCurator) -> ModuleCuratorResponse:
    return ModuleCuratorResponse(
        curator_id=curator.curator_id,
        learner_id=curator.learner_id,
        module_id=curator.module_id,
        cohort_id=curator.cohort_id,
        promoted_at=curator.promoted_at,
        promoted_by=curator.promoted_by,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/{cohort_id}/members/{learner_id}/validate-competency",
    response_model=CompetencyValidationResult,
)
def validate_topic_competency(
    cohort_id: str,
    learner_id: str,
    body: ValidateTopicCompetencyRequest,
    caller_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyUnitOfWork = Depends(get_cohort_uow),
) -> CompetencyValidationResult:
    """
    Validate whether a learner has achieved topic competency.

    Checks all 4 competency requirements:
    1. Completed all required practice tasks
    2. Passed knowledge check with minimum score
    3. Received at least one peer review
    4. Received mentor approval

    Authorization: Master or Module Curator only.
    """
    use_case = ValidateTopicCompetencyUseCase(uow)
    try:
        result = use_case.execute(
            learner_id=learner_id,
            topic_id=body.topic_id,
            cohort_id=cohort_id,
            caller_id=caller_id,
            knowledge_check_score=body.knowledge_check_score,
            mentor_approved=body.mentor_approved,
        )
        # Map ValidationResult to CompetencyValidationResult
        missing_steps = [step.value for step in result.failed_steps]
        return CompetencyValidationResult(
            topic_id=body.topic_id,
            is_validated=result.is_valid,
            missing_steps=missing_steps,
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post(
    "/{cohort_id}/members/{learner_id}/promote-expert",
    status_code=201,
    response_model=TopicExpertResponse,
)
def promote_to_topic_expert(
    cohort_id: str,
    learner_id: str,
    body: PromoteToTopicExpertRequest,
    caller_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyUnitOfWork = Depends(get_cohort_uow),
) -> TopicExpertResponse:
    """
    Promote a learner to Topic Expert for a specific topic.

    Prerequisites:
    - Learner must have achieved Topic Competency (4 steps)
    - Caller must be Master or Module Curator

    Authorization: Master or Module Curator only.
    """
    use_case = PromoteToTopicExpertUseCase(uow)
    try:
        expert = use_case.execute(
            expert_id=body.expert_id,
            cohort_id=cohort_id,
            learner_id=learner_id,
            topic_id=body.topic_id,
            validator_id=caller_id,
        )
        return _topic_expert_to_response(expert)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/{cohort_id}/members/{learner_id}/promote-curator",
    status_code=201,
    response_model=ModuleCuratorResponse,
)
def promote_to_module_curator(
    cohort_id: str,
    learner_id: str,
    body: PromoteToModuleCuratorRequest,
    caller_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyUnitOfWork = Depends(get_cohort_uow),
) -> ModuleCuratorResponse:
    """
    Promote a learner to Module Curator.

    Prerequisites:
    - Learner must be Topic Expert in all topics of the module
    - Helper metrics must meet thresholds (3 learners helped, 5 tasks reviewed, 4.0 avg satisfaction)
    - Caller must be Master

    Authorization: Master only.
    """
    use_case = PromoteToModuleCuratorUseCase(uow)
    try:
        curator = use_case.execute(
            curator_id=body.curator_id,
            cohort_id=cohort_id,
            learner_id=learner_id,
            module_id=body.module_id,
            caller_id=caller_id,
        )
        return _module_curator_to_response(curator)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{cohort_id}/helper-metrics", response_model=list[HelperMetricsResponse])
def get_cohort_helper_metrics(
    cohort_id: str,
    caller_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyUnitOfWork = Depends(get_cohort_uow),
) -> list[HelperMetricsResponse]:
    """
    Get helper metrics for all members in a cohort.

    Returns aggregated peer helping activity stats for each member.

    Authorization: Cohort member (Master, Curator, or Learner in the cohort).
    """
    with uow:
        cohort = uow.cohorts.find_by_id(cohort_id)
        if cohort is None:
            raise HTTPException(status_code=404, detail=f"Cohort {cohort_id} not found")

        # Check if caller is master or member
        is_master = cohort.master_id == caller_id
        is_member = any(m.learner_id == caller_id for m in cohort.memberships)
        if not (is_master or is_member):
            raise HTTPException(
                status_code=403,
                detail=f"User {caller_id} is not a member of cohort {cohort_id}",
            )

        metrics_list = uow.helper_metrics.find_by_cohort(cohort_id)
        return [_helper_metrics_to_response(m) for m in metrics_list]


@router.get("/{cohort_id}/topic-experts", response_model=list[TopicExpertResponse])
def get_cohort_topic_experts(
    cohort_id: str,
    caller_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyUnitOfWork = Depends(get_cohort_uow),
) -> list[TopicExpertResponse]:
    """
    List all Topic Experts in a cohort.

    Returns all learners who have been promoted to Topic Expert status
    for any topic in the cohort.

    Authorization: Cohort member (Master, Curator, or Learner in the cohort).
    """
    # Authorization check
    with uow:
        cohort = uow.cohorts.find_by_id(cohort_id)
        if cohort is None:
            raise HTTPException(status_code=404, detail=f"Cohort {cohort_id} not found")

        # Check if caller is master or member
        is_master = cohort.master_id == caller_id
        is_member = any(m.learner_id == caller_id for m in cohort.memberships)
        if not (is_master or is_member):
            raise HTTPException(
                status_code=403,
                detail=f"User {caller_id} is not a member of cohort {cohort_id}",
            )

        # Retrieve all topic experts
        experts = uow.topic_experts.find_by_cohort(cohort_id)
        return [_topic_expert_to_response(e) for e in experts]


@router.get(
    "/{cohort_id}/pending-competency-validations",
    response_model=list[PendingCompetencyValidationResponse],
)
def get_pending_competency_validations(
    cohort_id: str,
    caller_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyUnitOfWork = Depends(get_cohort_uow),
) -> list[PendingCompetencyValidationResponse]:
    """
    List learners waiting for competency knowledge-check validation.

    Returns PendingCompetencyValidation records where the learner has not yet
    been granted a TopicCompetency for the corresponding topic. Stale records
    (already validated) are filtered out dynamically.

    Authorization: Master or Module Curator only.
    """
    use_case = GetPendingCompetencyValidationsUseCase(uow)
    try:
        records = use_case.execute(cohort_id=cohort_id, caller_id=caller_id)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return [
        PendingCompetencyValidationResponse(
            pending_id=r.pending_id,
            learner_id=r.learner_id,
            topic_id=r.topic_id,
            cohort_id=r.cohort_id,
            created_at=r.created_at,
        )
        for r in records
    ]


@router.get(
    "/{cohort_id}/pending-curator-promotions",
    response_model=list[PendingCuratorPromotionResponse],
)
def get_pending_curator_promotions(
    cohort_id: str,
    caller_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyUnitOfWork = Depends(get_cohort_uow),
) -> list[PendingCuratorPromotionResponse]:
    """
    List learners eligible for Module Curator promotion.

    Returns PendingCuratorPromotion records where the learner has not yet been
    formally promoted to ModuleCurator. Stale records are filtered dynamically.

    Authorization: Master only.
    """
    use_case = GetPendingCuratorPromotionsUseCase(uow)
    try:
        records = use_case.execute(cohort_id=cohort_id, caller_id=caller_id)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return [
        PendingCuratorPromotionResponse(
            pending_id=r.pending_id,
            learner_id=r.learner_id,
            module_id=r.module_id,
            cohort_id=r.cohort_id,
            created_at=r.created_at,
        )
        for r in records
    ]
