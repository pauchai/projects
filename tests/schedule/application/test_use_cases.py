"""Unit tests for schedule application use cases."""

import pytest
from datetime import datetime, time, timezone, timedelta

from src.schedule.domain.curator import Curator
from src.schedule.domain.consultation_request import ConsultationRequest
from src.schedule.application.create_curator import CreateCuratorUseCase
from src.schedule.application.add_availability_slot import AddAvailabilitySlotUseCase
from src.schedule.application.submit_consultation_request import SubmitConsultationRequestUseCase
from src.schedule.application.start_negotiation import StartNegotiationUseCase
from src.schedule.application.respond_to_offer import RespondToOfferUseCase
from src.schedule.application.assign_appointment import AssignAppointmentUseCase
from tests.schedule.fakes.fake_unit_of_work import FakeScheduleUnitOfWork, FakeAiRecommender


def make_uow() -> FakeScheduleUnitOfWork:
    return FakeScheduleUnitOfWork()


def seed_curator(uow: FakeScheduleUnitOfWork, curator_id: str = "c-1", name: str = "Alice") -> Curator:
    curator = Curator(curator_id=curator_id, name=name, skills=["Python"])
    uow.curators.save(curator)
    return curator


def seed_request_pending(uow: FakeScheduleUnitOfWork, curator_ids: list[str]) -> ConsultationRequest:
    req = ConsultationRequest(
        request_id="r-1",
        student_name="Ivan",
        request_text="Need help with async Python",
    )
    req.set_recommendations(curator_ids)
    uow.requests.save(req)
    return req


# ---------------------------------------------------------------------------
# CreateCuratorUseCase
# ---------------------------------------------------------------------------

class TestCreateCuratorUseCase:
    def test_creates_curator_and_returns_id(self) -> None:
        uow = make_uow()
        use_case = CreateCuratorUseCase(uow)

        curator_id = use_case.execute(name="Alice", skills=["Python"])

        saved = uow.curators.find_by_id(curator_id)
        assert saved is not None
        assert saved.name == "Alice"
        assert "Python" in saved.skills
        assert uow.committed

    def test_creates_curator_without_skills(self) -> None:
        uow = make_uow()
        use_case = CreateCuratorUseCase(uow)

        curator_id = use_case.execute(name="Bob")

        saved = uow.curators.find_by_id(curator_id)
        assert saved is not None
        assert saved.skills == []

    def test_raises_when_name_empty(self) -> None:
        uow = make_uow()
        use_case = CreateCuratorUseCase(uow)

        with pytest.raises(ValueError, match="name"):
            use_case.execute(name="  ")


# ---------------------------------------------------------------------------
# AddAvailabilitySlotUseCase
# ---------------------------------------------------------------------------

class TestAddAvailabilitySlotUseCase:
    def test_adds_slot_to_curator(self) -> None:
        uow = make_uow()
        seed_curator(uow, curator_id="c-1")
        use_case = AddAvailabilitySlotUseCase(uow)

        slot_id = use_case.execute(
            curator_id="c-1",
            weekday=0,
            start_time=time(10, 0),
            end_time=time(12, 0),
        )

        curator = uow.curators.find_by_id("c-1")
        assert curator is not None
        assert len(curator.availability_slots) == 1
        assert curator.availability_slots[0].slot_id == slot_id

    def test_raises_when_curator_not_found(self) -> None:
        uow = make_uow()
        use_case = AddAvailabilitySlotUseCase(uow)

        with pytest.raises(LookupError, match="not found"):
            use_case.execute(
                curator_id="nonexistent",
                weekday=0,
                start_time=time(10, 0),
                end_time=time(12, 0),
            )

    def test_raises_on_overlapping_slot(self) -> None:
        uow = make_uow()
        seed_curator(uow, curator_id="c-1")
        use_case = AddAvailabilitySlotUseCase(uow)

        use_case.execute("c-1", weekday=0, start_time=time(10, 0), end_time=time(12, 0))
        with pytest.raises(ValueError, match="overlaps"):
            use_case.execute("c-1", weekday=0, start_time=time(11, 0), end_time=time(13, 0))


# ---------------------------------------------------------------------------
# SubmitConsultationRequestUseCase
# ---------------------------------------------------------------------------

class TestSubmitConsultationRequestUseCase:
    def test_creates_request_with_recommendations(self) -> None:
        uow = make_uow()
        seed_curator(uow, curator_id="c-1", name="Alice")
        recommender = FakeAiRecommender()
        use_case = SubmitConsultationRequestUseCase(uow, recommender)

        request_id = use_case.execute(
            student_name="Ivan",
            request_text="Need help with Python async",
        )

        saved = uow.requests.find_by_id(request_id)
        assert saved is not None
        assert saved.status == "pending"
        assert "c-1" in saved.recommended_curator_ids

    def test_creates_request_without_curators(self) -> None:
        uow = make_uow()
        recommender = FakeAiRecommender()
        use_case = SubmitConsultationRequestUseCase(uow, recommender)

        request_id = use_case.execute(
            student_name="Ivan",
            request_text="Need help",
        )

        saved = uow.requests.find_by_id(request_id)
        assert saved is not None
        assert saved.recommended_curator_ids == []

    def test_commits(self) -> None:
        uow = make_uow()
        recommender = FakeAiRecommender()
        use_case = SubmitConsultationRequestUseCase(uow, recommender)
        use_case.execute(student_name="Ivan", request_text="Help")
        assert uow.committed


# ---------------------------------------------------------------------------
# StartNegotiationUseCase
# ---------------------------------------------------------------------------

class TestStartNegotiationUseCase:
    def test_creates_offers_for_each_recommended_curator(self) -> None:
        uow = make_uow()
        seed_request_pending(uow, curator_ids=["c-1", "c-2"])
        use_case = StartNegotiationUseCase(uow)

        offer_ids = use_case.execute("r-1")

        assert len(offer_ids) == 2
        request = uow.requests.find_by_id("r-1")
        assert request is not None
        assert request.status == "negotiating"

    def test_raises_when_request_not_found(self) -> None:
        uow = make_uow()
        use_case = StartNegotiationUseCase(uow)

        with pytest.raises(LookupError, match="not found"):
            use_case.execute("nonexistent")

    def test_raises_when_no_recommendations(self) -> None:
        uow = make_uow()
        req = ConsultationRequest(request_id="r-1", student_name="Ivan", request_text="Help")
        uow.requests.save(req)
        use_case = StartNegotiationUseCase(uow)

        with pytest.raises(ValueError, match="recommended curators"):
            use_case.execute("r-1")


# ---------------------------------------------------------------------------
# RespondToOfferUseCase
# ---------------------------------------------------------------------------

class TestRespondToOfferUseCase:
    def _setup_negotiating(self, uow: FakeScheduleUnitOfWork) -> list[str]:
        seed_request_pending(uow, curator_ids=["c-1", "c-2"])
        start = StartNegotiationUseCase(uow)
        return start.execute("r-1")

    def test_accept_changes_offer_status(self) -> None:
        uow = make_uow()
        offer_ids = self._setup_negotiating(uow)
        use_case = RespondToOfferUseCase(uow)

        use_case.accept(offer_ids[0])

        offer = uow.offers.find_by_id(offer_ids[0])
        assert offer is not None
        assert offer.status == "accepted"

    def test_accept_cancels_other_pending_offers(self) -> None:
        uow = make_uow()
        offer_ids = self._setup_negotiating(uow)
        use_case = RespondToOfferUseCase(uow)

        use_case.accept(offer_ids[0])

        other = uow.offers.find_by_id(offer_ids[1])
        assert other is not None
        assert other.status == "declined"

    def test_decline_changes_offer_status(self) -> None:
        uow = make_uow()
        offer_ids = self._setup_negotiating(uow)
        use_case = RespondToOfferUseCase(uow)

        use_case.decline(offer_ids[0])

        offer = uow.offers.find_by_id(offer_ids[0])
        assert offer is not None
        assert offer.status == "declined"

    def test_raises_when_offer_not_found(self) -> None:
        uow = make_uow()
        use_case = RespondToOfferUseCase(uow)

        with pytest.raises(LookupError, match="not found"):
            use_case.accept("nonexistent")


# ---------------------------------------------------------------------------
# AssignAppointmentUseCase
# ---------------------------------------------------------------------------

class TestAssignAppointmentUseCase:
    def _setup_accepted_offer(self, uow: FakeScheduleUnitOfWork) -> None:
        seed_request_pending(uow, curator_ids=["c-1"])
        start = StartNegotiationUseCase(uow)
        offer_ids = start.execute("r-1")
        respond = RespondToOfferUseCase(uow)
        respond.accept(offer_ids[0])

    def test_creates_appointment_and_confirms_request(self) -> None:
        uow = make_uow()
        self._setup_accepted_offer(uow)
        use_case = AssignAppointmentUseCase(uow)
        scheduled_at = datetime.now(timezone.utc) + timedelta(days=2)

        appointment_id = use_case.execute("r-1", scheduled_at)

        appointment = uow.appointments.find_by_id(appointment_id)
        assert appointment is not None
        assert appointment.curator_id == "c-1"
        assert appointment.scheduled_at == scheduled_at

        request = uow.requests.find_by_id("r-1")
        assert request is not None
        assert request.status == "confirmed"

    def test_raises_when_request_not_found(self) -> None:
        uow = make_uow()
        use_case = AssignAppointmentUseCase(uow)
        scheduled_at = datetime.now(timezone.utc) + timedelta(days=2)

        with pytest.raises(LookupError, match="not found"):
            use_case.execute("nonexistent", scheduled_at)

    def test_raises_when_no_accepted_offer(self) -> None:
        uow = make_uow()
        seed_request_pending(uow, curator_ids=["c-1"])
        StartNegotiationUseCase(uow).execute("r-1")
        use_case = AssignAppointmentUseCase(uow)
        scheduled_at = datetime.now(timezone.utc) + timedelta(days=2)

        with pytest.raises(ValueError, match="No accepted offer"):
            use_case.execute("r-1", scheduled_at)

    def test_raises_when_request_not_negotiating(self) -> None:
        uow = make_uow()
        req = ConsultationRequest(request_id="r-1", student_name="Ivan", request_text="Help")
        uow.requests.save(req)
        use_case = AssignAppointmentUseCase(uow)
        scheduled_at = datetime.now(timezone.utc) + timedelta(days=2)

        with pytest.raises(ValueError, match="pending"):
            use_case.execute("r-1", scheduled_at)
