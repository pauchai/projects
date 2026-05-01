"""Unit tests for ConsultationRequest domain entity."""

import pytest

from src.schedule.domain.consultation_request import ConsultationRequest


def make_request(
    request_id: str = "r-1",
    student_name: str = "Ivan Petrov",
    request_text: str = "Need help with Python async programming",
) -> ConsultationRequest:
    return ConsultationRequest(
        request_id=request_id,
        student_name=student_name,
        request_text=request_text,
    )


class TestConsultationRequestCreation:
    def test_creates_with_pending_status(self) -> None:
        req = make_request()
        assert req.status == "pending"
        assert req.recommended_curator_ids == []

    def test_raises_when_student_name_empty(self) -> None:
        with pytest.raises(ValueError, match="Student name"):
            make_request(student_name="  ")

    def test_raises_when_request_text_empty(self) -> None:
        with pytest.raises(ValueError, match="Request text"):
            make_request(request_text="  ")

    def test_strips_whitespace(self) -> None:
        req = make_request(student_name="  Alice  ", request_text="  Help me  ")
        assert req.student_name == "Alice"
        assert req.request_text == "Help me"


class TestSetRecommendations:
    def test_sets_recommendations(self) -> None:
        req = make_request()
        req.set_recommendations(["c-1", "c-2"])
        assert req.recommended_curator_ids == ["c-1", "c-2"]

    def test_raises_when_empty_list(self) -> None:
        req = make_request()
        with pytest.raises(ValueError, match="empty"):
            req.set_recommendations([])


class TestStartNegotiation:
    def test_transitions_to_negotiating(self) -> None:
        req = make_request()
        req.set_recommendations(["c-1"])
        req.start_negotiation()
        assert req.status == "negotiating"

    def test_raises_without_recommendations(self) -> None:
        req = make_request()
        with pytest.raises(ValueError, match="recommended curators"):
            req.start_negotiation()

    def test_raises_when_already_negotiating(self) -> None:
        req = make_request()
        req.set_recommendations(["c-1"])
        req.start_negotiation()
        with pytest.raises(ValueError, match="negotiation"):
            req.start_negotiation()

    def test_raises_when_cancelled(self) -> None:
        req = make_request()
        req.cancel()
        with pytest.raises(ValueError, match="cancelled"):
            req.start_negotiation()


class TestConfirm:
    def test_transitions_to_confirmed(self) -> None:
        req = make_request()
        req.set_recommendations(["c-1"])
        req.start_negotiation()
        req.confirm()
        assert req.status == "confirmed"

    def test_raises_when_pending(self) -> None:
        req = make_request()
        with pytest.raises(ValueError, match="pending"):
            req.confirm()


class TestCancel:
    def test_cancels_from_pending(self) -> None:
        req = make_request()
        req.cancel()
        assert req.status == "cancelled"

    def test_cancels_from_negotiating(self) -> None:
        req = make_request()
        req.set_recommendations(["c-1"])
        req.start_negotiation()
        req.cancel()
        assert req.status == "cancelled"

    def test_raises_when_already_cancelled(self) -> None:
        req = make_request()
        req.cancel()
        with pytest.raises(ValueError, match="cancelled"):
            req.cancel()

    def test_raises_when_confirmed(self) -> None:
        req = make_request()
        req.set_recommendations(["c-1"])
        req.start_negotiation()
        req.confirm()
        with pytest.raises(ValueError, match="confirmed"):
            req.cancel()


class TestReopenNegotiation:
    def test_reopens_from_confirmed(self) -> None:
        req = make_request()
        req.set_recommendations(["c-1"])
        req.start_negotiation()
        req.confirm()
        req.reopen_negotiation()
        assert req.status == "negotiating"

    def test_raises_when_not_confirmed(self) -> None:
        req = make_request()
        with pytest.raises(ValueError, match="Cannot reopen negotiation"):
            req.reopen_negotiation()
