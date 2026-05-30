"""Unit tests for ConsultationOffer domain entity."""

import pytest

from src.schedule.domain.consultation_offer import ConsultationOffer


def make_offer(
    offer_id: str = "o-1",
    request_id: str = "r-1",
    curator_id: str = "c-1",
) -> ConsultationOffer:
    return ConsultationOffer(
        offer_id=offer_id,
        request_id=request_id,
        curator_id=curator_id,
    )


class TestConsultationOfferCreation:
    def test_creates_with_pending_status(self) -> None:
        offer = make_offer()
        assert offer.status == "pending"
        assert offer.responded_at is None


class TestAccept:
    def test_transitions_to_accepted(self) -> None:
        offer = make_offer()
        offer.accept()
        assert offer.status == "accepted"
        assert offer.responded_at is not None

    def test_raises_when_already_accepted(self) -> None:
        offer = make_offer()
        offer.accept()
        with pytest.raises(ValueError, match="accepted"):
            offer.accept()

    def test_raises_when_declined(self) -> None:
        offer = make_offer()
        offer.decline()
        with pytest.raises(ValueError, match="declined"):
            offer.accept()


class TestDecline:
    def test_transitions_to_declined(self) -> None:
        offer = make_offer()
        offer.decline()
        assert offer.status == "declined"
        assert offer.responded_at is not None

    def test_raises_when_already_declined(self) -> None:
        offer = make_offer()
        offer.decline()
        with pytest.raises(ValueError, match="declined"):
            offer.decline()


class TestCancel:
    def test_cancels_pending_offer(self) -> None:
        offer = make_offer()
        offer.cancel()
        assert offer.status == "declined"

    def test_raises_when_already_accepted(self) -> None:
        offer = make_offer()
        offer.accept()
        with pytest.raises(ValueError, match="accepted"):
            offer.cancel()
