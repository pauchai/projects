"""Practice tasks routes: REST endpoints for the Cohort Learning peer review system."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from cohort_learning.api.dependencies import get_cohort_uow, get_current_user_id
from cohort_learning.api.schemas import (
    CreatePracticeTaskRequest,
    PeerReviewResponse,
    PracticeTaskResponse,
    ReviewScoreResponse,
    SubmitPeerReviewRequest,
    SubmitTaskSolutionRequest,
    TaskSubmissionResponse,
)
from cohort_learning.application.activate_practice_task import (
    ActivatePracticeTaskUseCase,
)
from cohort_learning.application.close_practice_task import ClosePracticeTaskUseCase
from cohort_learning.application.create_practice_task import CreatePracticeTaskUseCase
from cohort_learning.application.get_cohort_tasks import GetCohortTasksUseCase
from cohort_learning.application.submit_peer_review import SubmitPeerReviewUseCase
from cohort_learning.application.submit_task_solution import SubmitTaskSolutionUseCase
from cohort_learning.domain.peer_review import PeerReview
from cohort_learning.domain.practice_task import PracticeTask
from cohort_learning.domain.review_score import ReviewScore
from cohort_learning.infrastructure.sqlalchemy_unit_of_work import (
    SqlAlchemyUnitOfWork,
)

router = APIRouter(tags=["practice-tasks"])


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------


def _task_to_response(task: PracticeTask) -> PracticeTaskResponse:
    """Convert PracticeTask domain aggregate to PracticeTaskResponse."""
    return PracticeTaskResponse(
        task_id=task.task_id,
        cohort_id=task.cohort_id,
        topic_id=task.topic_id,
        creator_id=task.creator_id,
        title=task.title,
        description=task.description,
        status=task.status.value,
        created_at=task.created_at,
        submissions=[
            TaskSubmissionResponse(
                submission_id=s.submission_id,
                task_id=s.task_id,
                learner_id=s.learner_id,
                content=s.content,
                status=s.status.value,
                submitted_at=s.submitted_at,
            )
            for s in task.submissions
        ],
    )


def _review_to_response(review: PeerReview) -> PeerReviewResponse:
    """Convert PeerReview domain aggregate to PeerReviewResponse."""
    return PeerReviewResponse(
        review_id=review.review_id,
        submission_id=review.submission_id,
        reviewer_id=review.reviewer_id,
        task_id=review.task_id,
        cohort_id=review.cohort_id,
        status=review.status.value,
        overall_feedback=review.overall_feedback,
        created_at=review.created_at,
        reviewed_at=review.reviewed_at,
        scores=[
            ReviewScoreResponse(
                criterion=s.criterion,
                score=s.score,
                comment=s.comment,
            )
            for s in review.scores
        ],
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/cohorts/{cohort_id}/tasks",
    status_code=status.HTTP_201_CREATED,
    response_model=PracticeTaskResponse,
)
def create_practice_task(
    cohort_id: str,
    body: CreatePracticeTaskRequest,
    caller_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyUnitOfWork = Depends(get_cohort_uow),
) -> PracticeTaskResponse:
    """Create a new practice task for a cohort.

    Authorization: Master or Module Curator of the cohort.
    """
    use_case = CreatePracticeTaskUseCase(uow)
    task = use_case.execute(
        task_id=body.task_id,
        cohort_id=cohort_id,
        topic_id=body.topic_id,
        creator_id=caller_id,
        title=body.title,
        description=body.description,
    )
    return _task_to_response(task)


@router.get("/cohorts/{cohort_id}/tasks", response_model=list[PracticeTaskResponse])
def get_cohort_tasks(
    cohort_id: str,
    caller_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyUnitOfWork = Depends(get_cohort_uow),
) -> list[PracticeTaskResponse]:
    """List all practice tasks in a cohort.

    Authorization: Any cohort member.
    """
    use_case = GetCohortTasksUseCase(uow)
    tasks = use_case.execute(cohort_id=cohort_id, caller_id=caller_id)
    return [_task_to_response(task) for task in tasks]


@router.post(
    "/cohorts/{cohort_id}/tasks/{task_id}/activate",
    response_model=PracticeTaskResponse,
)
def activate_practice_task(
    cohort_id: str,
    task_id: str,
    caller_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyUnitOfWork = Depends(get_cohort_uow),
) -> PracticeTaskResponse:
    """Activate a practice task (Draft → Active).

    Authorization: Master or Module Curator.
    """
    use_case = ActivatePracticeTaskUseCase(uow)
    task = use_case.execute(task_id=task_id, caller_id=caller_id)
    return _task_to_response(task)


@router.post(
    "/cohorts/{cohort_id}/tasks/{task_id}/close", response_model=PracticeTaskResponse
)
def close_practice_task(
    cohort_id: str,
    task_id: str,
    caller_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyUnitOfWork = Depends(get_cohort_uow),
) -> PracticeTaskResponse:
    """Close a practice task (Draft/Active → Closed).

    Authorization: Master or Module Curator.
    """
    use_case = ClosePracticeTaskUseCase(uow)
    task = use_case.execute(task_id=task_id, caller_id=caller_id)
    return _task_to_response(task)


@router.post(
    "/cohorts/{cohort_id}/tasks/{task_id}/submissions",
    status_code=status.HTTP_201_CREATED,
    response_model=TaskSubmissionResponse,
)
def submit_task_solution(
    cohort_id: str,
    task_id: str,
    body: SubmitTaskSolutionRequest,
    caller_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyUnitOfWork = Depends(get_cohort_uow),
) -> TaskSubmissionResponse:
    """Submit a solution for a practice task.

    Authorization: Any cohort member (except the task creator).
    """
    use_case = SubmitTaskSolutionUseCase(uow)
    submission = use_case.execute(
        task_id=task_id,
        learner_id=caller_id,
        submission_id=body.submission_id,
        content=body.content,
    )
    return TaskSubmissionResponse(
        submission_id=submission.submission_id,
        task_id=submission.task_id,
        learner_id=submission.learner_id,
        content=submission.content,
        status=submission.status.value,
        submitted_at=submission.submitted_at,
    )


@router.post(
    "/cohorts/{cohort_id}/tasks/{task_id}/submissions/{submission_id}/reviews",
    status_code=status.HTTP_201_CREATED,
    response_model=PeerReviewResponse,
)
def submit_peer_review(
    cohort_id: str,
    task_id: str,
    submission_id: str,
    body: SubmitPeerReviewRequest,
    caller_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyUnitOfWork = Depends(get_cohort_uow),
) -> PeerReviewResponse:
    """Submit a peer review for a task submission.

    Authorization: Any cohort member (except the submission author).
    """
    use_case = SubmitPeerReviewUseCase(uow)
    review = use_case.execute(
        review_id=body.review_id,
        submission_id=submission_id,
        reviewer_id=caller_id,
        task_id=task_id,
        scores=[
            ReviewScore(
                criterion=s.criterion,
                score=s.score,
                comment=s.comment,
            )
            for s in body.scores
        ],
        overall_feedback=body.overall_feedback,
    )
    return _review_to_response(review)
