"""Cohort routes: REST endpoints for the Cohort Learning API."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from cohort_learning.api.dependencies import get_cohort_uow, get_current_user_id
from cohort_learning.api.schemas import (
    CohortMembershipResponse,
    CohortResponse,
    EnrolLearnerRequest,
    FormCohortRequest,
    MessageResponse,
)
from cohort_learning.application.change_cohort_status import (
    ActivateCohortUseCase,
    BeginCompletingCohortUseCase,
    CancelCohortUseCase,
    GraduateCohortUseCase,
)
from cohort_learning.application.enrol_learner import EnrolLearnerUseCase
from cohort_learning.application.form_cohort import FormCohortUseCase
from cohort_learning.application.list_my_cohorts import ListMyCohortsUseCase
from cohort_learning.application.remove_learner import RemoveLearnerUseCase
from cohort_learning.domain.learning_cohort import LearningCohort
from cohort_learning.infrastructure.sqlalchemy_unit_of_work import (
    SqlAlchemyUnitOfWork,
)

router = APIRouter(prefix="/cohorts", tags=["cohorts"])


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------


def _cohort_to_response(cohort: LearningCohort) -> CohortResponse:
    return CohortResponse(
        cohort_id=cohort.cohort_id,
        master_id=cohort.master_id,
        module_id=cohort.module_id,
        status=cohort.status.value,
        formed_at=cohort.formed_at,
        memberships=[
            CohortMembershipResponse(
                membership_id=m.membership_id,
                learner_id=m.learner_id,
                cohort_id=m.cohort_id,
                role=m.role.value,
                is_active=m.is_active,
                joined_at=m.joined_at,
            )
            for m in cohort.memberships
        ],
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("", status_code=201, response_model=CohortResponse)
def form_cohort(
    body: FormCohortRequest,
    caller_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyUnitOfWork = Depends(get_cohort_uow),
) -> CohortResponse:
    """Form a new learning cohort. The caller becomes the master."""
    use_case = FormCohortUseCase(uow)
    cohort = use_case.execute(
        cohort_id=body.cohort_id,
        master_id=caller_id,
        module_id=body.module_id,
    )
    return _cohort_to_response(cohort)


@router.get("", response_model=list[CohortResponse])
def list_my_cohorts(
    caller_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyUnitOfWork = Depends(get_cohort_uow),
) -> list[CohortResponse]:
    """List all cohorts where the caller is master or active member."""
    use_case = ListMyCohortsUseCase(uow)
    cohorts = use_case.execute(caller_id=caller_id)
    return [_cohort_to_response(c) for c in cohorts]


@router.get("/{cohort_id}", response_model=CohortResponse)
def get_cohort(
    cohort_id: str,
    uow: SqlAlchemyUnitOfWork = Depends(get_cohort_uow),
) -> CohortResponse:
    """Get a cohort by ID."""
    with uow:
        cohort = uow.cohorts.find_by_id(cohort_id)
        if cohort is None:
            raise LookupError(f"Cohort {cohort_id} not found")
        return _cohort_to_response(cohort)


@router.post("/{cohort_id}/learners", status_code=201, response_model=MessageResponse)
def enrol_learner(
    cohort_id: str,
    body: EnrolLearnerRequest,
    caller_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyUnitOfWork = Depends(get_cohort_uow),
) -> MessageResponse:
    """Enrol a learner into a forming cohort. Only the master can enrol."""
    use_case = EnrolLearnerUseCase(uow)
    use_case.execute(
        cohort_id=cohort_id,
        membership_id=body.membership_id,
        learner_id=body.learner_id,
        caller_id=caller_id,
    )
    return MessageResponse(message="Learner enrolled")


@router.delete("/{cohort_id}/learners/{membership_id}", response_model=MessageResponse)
def remove_learner(
    cohort_id: str,
    membership_id: str,
    caller_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyUnitOfWork = Depends(get_cohort_uow),
) -> MessageResponse:
    """Remove a learner from a cohort. Only the master can remove."""
    use_case = RemoveLearnerUseCase(uow)
    use_case.execute(
        cohort_id=cohort_id,
        membership_id=membership_id,
        caller_id=caller_id,
    )
    return MessageResponse(message="Learner removed")


@router.post("/{cohort_id}/activate", response_model=MessageResponse)
def activate_cohort(
    cohort_id: str,
    caller_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyUnitOfWork = Depends(get_cohort_uow),
) -> MessageResponse:
    """Activate a cohort (Forming -> Active). Requires minimum learner count."""
    use_case = ActivateCohortUseCase(uow)
    use_case.execute(cohort_id=cohort_id, caller_id=caller_id)
    return MessageResponse(message="Cohort activated")


@router.post("/{cohort_id}/begin-completing", response_model=MessageResponse)
def begin_completing_cohort(
    cohort_id: str,
    caller_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyUnitOfWork = Depends(get_cohort_uow),
) -> MessageResponse:
    """Begin completing a cohort (Active -> Completing)."""
    use_case = BeginCompletingCohortUseCase(uow)
    use_case.execute(cohort_id=cohort_id, caller_id=caller_id)
    return MessageResponse(message="Cohort is now completing")


@router.post("/{cohort_id}/graduate", response_model=MessageResponse)
def graduate_cohort(
    cohort_id: str,
    caller_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyUnitOfWork = Depends(get_cohort_uow),
) -> MessageResponse:
    """Graduate a cohort (Completing -> Graduated)."""
    use_case = GraduateCohortUseCase(uow)
    use_case.execute(cohort_id=cohort_id, caller_id=caller_id)
    return MessageResponse(message="Cohort graduated")


@router.post("/{cohort_id}/cancel", response_model=MessageResponse)
def cancel_cohort(
    cohort_id: str,
    caller_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyUnitOfWork = Depends(get_cohort_uow),
) -> MessageResponse:
    """Cancel a cohort (Forming/Active/Completing -> Cancelled)."""
    use_case = CancelCohortUseCase(uow)
    use_case.execute(cohort_id=cohort_id, caller_id=caller_id)
    return MessageResponse(message="Cohort cancelled")
