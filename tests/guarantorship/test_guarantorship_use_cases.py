"""Unit tests for Guarantorship use cases."""

from __future__ import annotations

import pytest
from decimal import Decimal

from guarantorship.application.accept_guarantee_request import (
    AcceptGuaranteeRequestCommand,
    AcceptGuaranteeRequestUseCase,
)
from guarantorship.application.create_zero_circle import (
    CreateZeroCircleCommand,
    CreateZeroCircleUseCase,
)
from guarantorship.application.join_zero_circle import (
    JoinZeroCircleCommand,
    JoinZeroCircleUseCase,
)
from guarantorship.application.reject_guarantee_request import (
    RejectGuaranteeRequestCommand,
    RejectGuaranteeRequestUseCase,
)
from guarantorship.application.request_guarantor import (
    RequestGuarantorCommand,
    RequestGuarantorUseCase,
)
from guarantorship.domain.guarantee_request import GuaranteeRequestStatus
from guarantorship.domain.zero_circle import ZeroCircleStatus
from tests.guarantorship.fakes import FakeGuarantorshipUnitOfWork


# ─── RequestGuarantor ─────────────────────────────────────────────────────────

class TestRequestGuarantorUseCase:
    def test_creates_pending_request(self) -> None:
        uow = FakeGuarantorshipUnitOfWork()
        use_case = RequestGuarantorUseCase(uow)

        result = use_case.execute(
            RequestGuarantorCommand(ward_id="ward-1", guarantor_id="guarantor-1")
        )

        assert result.ward_id == "ward-1"
        assert result.guarantor_id == "guarantor-1"
        assert result.status == GuaranteeRequestStatus.PENDING
        assert uow.committed

    def test_request_with_message(self) -> None:
        uow = FakeGuarantorshipUnitOfWork()
        result = RequestGuarantorUseCase(uow).execute(
            RequestGuarantorCommand(
                ward_id="ward-1",
                guarantor_id="guarantor-1",
                message="Please vouch for me",
            )
        )
        assert result.message == "Please vouch for me"

    def test_cannot_request_self(self) -> None:
        uow = FakeGuarantorshipUnitOfWork()
        with pytest.raises(ValueError, match="cannot"):
            RequestGuarantorUseCase(uow).execute(
                RequestGuarantorCommand(ward_id="user-1", guarantor_id="user-1")
            )


# ─── AcceptGuaranteeRequest ───────────────────────────────────────────────────

class TestAcceptGuaranteeRequestUseCase:
    def _make_pending_request(self, uow: FakeGuarantorshipUnitOfWork, request_id: str) -> None:
        from guarantorship.domain.guarantee_request import GuaranteeRequest
        req = GuaranteeRequest(
            request_id=request_id,
            ward_id="ward-1",
            guarantor_id="guarantor-1",
        )
        uow.requests.save(req)

    def test_accepts_pending_request(self) -> None:
        uow = FakeGuarantorshipUnitOfWork()
        self._make_pending_request(uow, "req-1")

        AcceptGuaranteeRequestUseCase(uow).execute(
            AcceptGuaranteeRequestCommand(request_id="req-1", guarantor_id="guarantor-1")
        )

        saved = uow.requests.find_by_id("req-1")
        assert saved is not None
        assert saved.status == GuaranteeRequestStatus.ACCEPTED

    def test_raises_when_request_not_found(self) -> None:
        uow = FakeGuarantorshipUnitOfWork()
        with pytest.raises(LookupError):
            AcceptGuaranteeRequestUseCase(uow).execute(
                AcceptGuaranteeRequestCommand(request_id="missing", guarantor_id="g-1")
            )

    def test_raises_when_wrong_guarantor(self) -> None:
        uow = FakeGuarantorshipUnitOfWork()
        self._make_pending_request(uow, "req-1")
        with pytest.raises(PermissionError):
            AcceptGuaranteeRequestUseCase(uow).execute(
                AcceptGuaranteeRequestCommand(request_id="req-1", guarantor_id="intruder")
            )


# ─── RejectGuaranteeRequest ───────────────────────────────────────────────────

class TestRejectGuaranteeRequestUseCase:
    def test_rejects_pending_request(self) -> None:
        uow = FakeGuarantorshipUnitOfWork()
        from guarantorship.domain.guarantee_request import GuaranteeRequest
        uow.requests.save(
            GuaranteeRequest(request_id="req-1", ward_id="w-1", guarantor_id="g-1")
        )

        RejectGuaranteeRequestUseCase(uow).execute(
            RejectGuaranteeRequestCommand(request_id="req-1", guarantor_id="g-1")
        )

        saved = uow.requests.find_by_id("req-1")
        assert saved is not None
        assert saved.status == GuaranteeRequestStatus.REJECTED


# ─── CreateZeroCircle ─────────────────────────────────────────────────────────

class TestCreateZeroCircleUseCase:
    def test_creates_open_circle_with_initiator_as_member(self) -> None:
        uow = FakeGuarantorshipUnitOfWork()
        circle = CreateZeroCircleUseCase(uow).execute(
            CreateZeroCircleCommand(initiated_by="user-1", name="Test Circle")
        )

        assert circle.status == ZeroCircleStatus.OPEN
        assert "user-1" in circle.member_ids()
        assert uow.committed

    def test_creates_circle_with_deposit_stub(self) -> None:
        uow = FakeGuarantorshipUnitOfWork()
        circle = CreateZeroCircleUseCase(uow).execute(
            CreateZeroCircleCommand(
                initiated_by="user-1",
                name="Deposit Circle",
                deposit_stub=Decimal("100.00"),
            )
        )
        assert circle.deposit_stub == Decimal("100.00")

    def test_raises_when_user_already_in_open_circle(self) -> None:
        uow = FakeGuarantorshipUnitOfWork()
        uc = CreateZeroCircleUseCase(uow)
        uc.execute(CreateZeroCircleCommand(initiated_by="user-1", name="First Circle"))

        with pytest.raises(ValueError, match="already a member"):
            uc.execute(CreateZeroCircleCommand(initiated_by="user-1", name="Second Circle"))


# ─── JoinZeroCircle ───────────────────────────────────────────────────────────

class TestJoinZeroCircleUseCase:
    def _create_circle(self, uow: FakeGuarantorshipUnitOfWork, initiator: str) -> str:
        circle = CreateZeroCircleUseCase(uow).execute(
            CreateZeroCircleCommand(initiated_by=initiator, name="Circle")
        )
        return circle.circle_id

    def test_joins_open_circle(self) -> None:
        uow = FakeGuarantorshipUnitOfWork()
        circle_id = self._create_circle(uow, "user-1")

        JoinZeroCircleUseCase(uow).execute(
            JoinZeroCircleCommand(circle_id=circle_id, user_id="user-2")
        )

        circle = uow.circles.find_by_id(circle_id)
        assert circle is not None
        assert "user-2" in circle.member_ids()

    def test_raises_when_circle_not_found(self) -> None:
        uow = FakeGuarantorshipUnitOfWork()
        with pytest.raises(LookupError):
            JoinZeroCircleUseCase(uow).execute(
                JoinZeroCircleCommand(circle_id="missing", user_id="user-1")
            )

    def test_raises_when_user_already_in_another_circle(self) -> None:
        uow = FakeGuarantorshipUnitOfWork()
        first_id = self._create_circle(uow, "user-1")
        second_id = self._create_circle(uow, "user-2")

        # user-3 joins first circle
        JoinZeroCircleUseCase(uow).execute(
            JoinZeroCircleCommand(circle_id=first_id, user_id="user-3")
        )

        # user-3 tries to join second circle — should fail
        with pytest.raises(ValueError, match="already a member"):
            JoinZeroCircleUseCase(uow).execute(
                JoinZeroCircleCommand(circle_id=second_id, user_id="user-3")
            )
