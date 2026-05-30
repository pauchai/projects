"""Schedule domain ports (driven interfaces)."""

from typing import Protocol

from schedule.domain.appointment import Appointment
from schedule.domain.consultation_offer import ConsultationOffer
from schedule.domain.consultation_request import ConsultationRequest
from schedule.domain.curator import Curator


class CuratorRepository(Protocol):
    """Persistence port for Curator aggregate."""

    def find_by_id(self, curator_id: str) -> Curator | None: ...
    def find_all(self) -> list[Curator]: ...
    def save(self, curator: Curator) -> None: ...


class ConsultationRequestRepository(Protocol):
    """Persistence port for ConsultationRequest aggregate."""

    def find_by_id(self, request_id: str) -> ConsultationRequest | None: ...
    def find_all(self) -> list[ConsultationRequest]: ...
    def save(self, request: ConsultationRequest) -> None: ...


class ConsultationOfferRepository(Protocol):
    """Persistence port for ConsultationOffer."""

    def find_by_id(self, offer_id: str) -> ConsultationOffer | None: ...
    def find_by_request_id(self, request_id: str) -> list[ConsultationOffer]: ...
    def save(self, offer: ConsultationOffer) -> None: ...
    def save_many(self, offers: list[ConsultationOffer]) -> None: ...


class AppointmentRepository(Protocol):
    """Persistence port for Appointment."""

    def find_by_id(self, appointment_id: str) -> Appointment | None: ...
    def find_by_request_id(self, request_id: str) -> Appointment | None: ...
    def save(self, appointment: Appointment) -> None: ...


class AiRecommender(Protocol):
    """Port for the AI curator recommender.

    The stub implementation returns curators sorted by naive keyword
    matching. The real implementation will call an LLM API.
    """

    def recommend(
        self,
        request_text: str,
        curators: list[Curator],
    ) -> list[str]:
        """Return an ordered list of curator_ids by relevance."""
        ...


class ScheduleUnitOfWork(Protocol):
    """Unit of Work for the Schedule bounded context."""

    curators: CuratorRepository
    requests: ConsultationRequestRepository
    offers: ConsultationOfferRepository
    appointments: AppointmentRepository

    def __enter__(self) -> "ScheduleUnitOfWork": ...
    def __exit__(self, *args: object) -> None: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...
