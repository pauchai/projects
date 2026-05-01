"""Use case: Submit a student consultation request."""

import uuid

from schedule.domain.consultation_request import ConsultationRequest
from schedule.domain.ports import AiRecommender, ScheduleUnitOfWork


class SubmitConsultationRequestUseCase:
    """Student submits a free-text consultation request.

    The AI recommender (stub) immediately suggests matching curators.
    """

    def __init__(self, uow: ScheduleUnitOfWork, recommender: AiRecommender) -> None:
        self._uow = uow
        self._recommender = recommender

    def execute(self, student_name: str, request_text: str) -> str:
        """Create request, attach recommendations, return request_id."""
        with self._uow as uow:
            request = ConsultationRequest(
                request_id=str(uuid.uuid4()),
                student_name=student_name,
                request_text=request_text,
            )

            curators = uow.curators.find_all()
            if curators:
                recommended_ids = self._recommender.recommend(request_text, curators)
                if recommended_ids:
                    request.set_recommendations(recommended_ids)

            uow.requests.save(request)
            uow.commit()
            return request.request_id
