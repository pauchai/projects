"""Fake implementations for schedule unit tests."""

from src.schedule.domain.appointment import Appointment
from src.schedule.domain.consultation_offer import ConsultationOffer
from src.schedule.domain.consultation_request import ConsultationRequest
from src.schedule.domain.curator import Curator


class FakeCuratorRepository:
    def __init__(self) -> None:
        self._store: dict[str, Curator] = {}

    def find_by_id(self, curator_id: str) -> Curator | None:
        return self._store.get(curator_id)

    def find_all(self) -> list[Curator]:
        return list(self._store.values())

    def save(self, curator: Curator) -> None:
        self._store[curator.curator_id] = curator


class FakeConsultationRequestRepository:
    def __init__(self) -> None:
        self._store: dict[str, ConsultationRequest] = {}

    def find_by_id(self, request_id: str) -> ConsultationRequest | None:
        return self._store.get(request_id)

    def find_all(self) -> list[ConsultationRequest]:
        return list(self._store.values())

    def save(self, request: ConsultationRequest) -> None:
        self._store[request.request_id] = request


class FakeConsultationOfferRepository:
    def __init__(self) -> None:
        self._store: dict[str, ConsultationOffer] = {}

    def find_by_id(self, offer_id: str) -> ConsultationOffer | None:
        return self._store.get(offer_id)

    def find_by_request_id(self, request_id: str) -> list[ConsultationOffer]:
        return [o for o in self._store.values() if o.request_id == request_id]

    def save(self, offer: ConsultationOffer) -> None:
        self._store[offer.offer_id] = offer

    def save_many(self, offers: list[ConsultationOffer]) -> None:
        for offer in offers:
            self.save(offer)


class FakeAppointmentRepository:
    def __init__(self) -> None:
        self._store: dict[str, Appointment] = {}

    def find_by_id(self, appointment_id: str) -> Appointment | None:
        return self._store.get(appointment_id)

    def find_by_request_id(self, request_id: str) -> Appointment | None:
        for appt in self._store.values():
            if appt.request_id == request_id:
                return appt
        return None

    def save(self, appointment: Appointment) -> None:
        self._store[appointment.appointment_id] = appointment


class FakeAiRecommender:
    """Stub recommender: returns all curator_ids in insertion order."""

    def recommend(self, request_text: str, curators: list[Curator]) -> list[str]:
        return [c.curator_id for c in curators]


class FakeScheduleUnitOfWork:
    def __init__(self) -> None:
        self.curators = FakeCuratorRepository()
        self.requests = FakeConsultationRequestRepository()
        self.offers = FakeConsultationOfferRepository()
        self.appointments = FakeAppointmentRepository()
        self.committed = False

    def __enter__(self) -> "FakeScheduleUnitOfWork":
        return self

    def __exit__(self, *args: object) -> None:
        pass

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        pass
