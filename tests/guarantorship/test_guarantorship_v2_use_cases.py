"""Unit tests for Guarantorship v2 use cases (deposits, deals, complaints, settings)."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from guarantorship.application.cast_vote import CastVoteCommand, CastVoteUseCase
from guarantorship.application.create_deal import CreateDealCommand, CreateDealUseCase
from guarantorship.application.create_deposit import CreateDepositCommand, CreateDepositUseCase
from guarantorship.application.escalate_complaint import (
    EscalateComplaintCommand,
    EscalateComplaintUseCase,
)
from guarantorship.application.file_complaint import FileComplaintCommand, FileComplaintUseCase
from guarantorship.application.platform_settings import (
    GetPlatformSettingsUseCase,
    UpdatePlatformSettingsCommand,
    UpdatePlatformSettingsUseCase,
)
from guarantorship.domain.complaint import Complaint, ComplaintStatus, Verdict
from guarantorship.domain.deal import Deal, DealStatus
from guarantorship.domain.guarantorship import Guarantorship
from tests.guarantorship.fakes import FakeGuarantorshipUnitOfWork


# ─── helpers ─────────────────────────────────────────────────────────────────


def _make_guarantorship(uow: FakeGuarantorshipUnitOfWork, guarantor_id: str, ward_id: str) -> None:
    uow.guarantorships.save(
        Guarantorship(
            guarantorship_id=str(uuid.uuid4()),
            guarantor_id=guarantor_id,
            ward_id=ward_id,
            request_id=str(uuid.uuid4()),
            created_at=datetime.now(timezone.utc),
        )
    )


def _make_deal(
    uow: FakeGuarantorshipUnitOfWork,
    deal_id: str = "deal-1",
    initiator: str = "alice",
    counterparty: str = "bob",
) -> Deal:
    deal = Deal(
        deal_id=deal_id,
        initiator_id=initiator,
        counterparty_id=counterparty,
        amount=Decimal("100"),
        status=DealStatus.ACTIVE,
        created_at=datetime.now(timezone.utc),
    )
    uow.deals.save(deal)
    return deal


def _make_complaint(
    uow: FakeGuarantorshipUnitOfWork,
    status: ComplaintStatus = ComplaintStatus.VOTING,
    escalation_level: int = 0,
    deadline_past: bool = False,
) -> Complaint:
    deadline = (
        datetime.now(timezone.utc) - timedelta(days=1)
        if deadline_past
        else datetime.now(timezone.utc) + timedelta(days=7)
    )
    c = Complaint(
        complaint_id="complaint-1",
        deal_id="deal-1",
        filed_by_id="alice",
        against_id="bob",
        description="bad actor",
        status=status,
        verdict=None,
        voting_deadline=deadline,
        escalation_level=escalation_level,
        created_at=datetime.now(timezone.utc),
    )
    uow.complaints.save(c)
    return c


# ─── CreateDeposit ────────────────────────────────────────────────────────────


class TestCreateDepositUseCase:
    def test_creates_deposit_with_active_guarantor(self) -> None:
        uow = FakeGuarantorshipUnitOfWork()
        _make_guarantorship(uow, guarantor_id="guarantor-1", ward_id="ward-1")

        deposit = CreateDepositUseCase(uow).execute(
            CreateDepositCommand(
                ward_id="ward-1",
                guarantor_id="guarantor-1",
                amount=Decimal("50"),
            )
        )

        assert deposit.ward_id == "ward-1"
        assert deposit.guarantor_id == "guarantor-1"
        assert deposit.amount == Decimal("50")
        assert deposit.blockchain_ref is None
        assert uow.committed

    def test_stores_blockchain_ref(self) -> None:
        uow = FakeGuarantorshipUnitOfWork()
        _make_guarantorship(uow, guarantor_id="g-1", ward_id="w-1")

        deposit = CreateDepositUseCase(uow).execute(
            CreateDepositCommand(
                ward_id="w-1",
                guarantor_id="g-1",
                amount=Decimal("10"),
                blockchain_ref="0xdeadbeef",
            )
        )

        assert deposit.blockchain_ref == "0xdeadbeef"

    def test_raises_when_not_guarantor(self) -> None:
        uow = FakeGuarantorshipUnitOfWork()
        # no guarantorship exists

        with pytest.raises(PermissionError, match="active guarantor"):
            CreateDepositUseCase(uow).execute(
                CreateDepositCommand(ward_id="w-1", guarantor_id="stranger", amount=Decimal("10"))
            )

    def test_raises_when_amount_zero_or_negative(self) -> None:
        uow = FakeGuarantorshipUnitOfWork()
        _make_guarantorship(uow, guarantor_id="g-1", ward_id="w-1")

        with pytest.raises(ValueError, match="positive"):
            CreateDepositUseCase(uow).execute(
                CreateDepositCommand(ward_id="w-1", guarantor_id="g-1", amount=Decimal("0"))
            )


# ─── CreateDeal ───────────────────────────────────────────────────────────────


class TestCreateDealUseCase:
    def test_creates_deal(self) -> None:
        uow = FakeGuarantorshipUnitOfWork()

        deal = CreateDealUseCase(uow).execute(
            CreateDealCommand(
                initiator_id="alice",
                counterparty_id="bob",
                amount=Decimal("200"),
            )
        )

        assert deal.initiator_id == "alice"
        assert deal.counterparty_id == "bob"
        assert deal.amount == Decimal("200")
        assert deal.status == DealStatus.PENDING
        assert uow.committed

    def test_raises_when_same_participants(self) -> None:
        uow = FakeGuarantorshipUnitOfWork()

        with pytest.raises(ValueError, match="different"):
            CreateDealUseCase(uow).execute(
                CreateDealCommand(
                    initiator_id="alice",
                    counterparty_id="alice",
                    amount=Decimal("100"),
                )
            )


# ─── FileComplaint ────────────────────────────────────────────────────────────


class TestFileComplaintUseCase:
    def test_files_complaint(self) -> None:
        uow = FakeGuarantorshipUnitOfWork()
        _make_deal(uow)

        complaint = FileComplaintUseCase(uow).execute(
            FileComplaintCommand(
                deal_id="deal-1",
                filed_by_id="alice",
                against_id="bob",
                description="they cheated",
            )
        )

        assert complaint.filed_by_id == "alice"
        assert complaint.against_id == "bob"
        assert complaint.status == ComplaintStatus.VOTING
        assert complaint.voting_deadline is not None
        assert uow.committed

    def test_raises_when_deal_not_found(self) -> None:
        uow = FakeGuarantorshipUnitOfWork()

        with pytest.raises(LookupError):
            FileComplaintUseCase(uow).execute(
                FileComplaintCommand(
                    deal_id="missing",
                    filed_by_id="alice",
                    against_id="bob",
                    description="x",
                )
            )

    def test_raises_when_not_participant(self) -> None:
        uow = FakeGuarantorshipUnitOfWork()
        _make_deal(uow)

        with pytest.raises(PermissionError, match="participants"):
            FileComplaintUseCase(uow).execute(
                FileComplaintCommand(
                    deal_id="deal-1",
                    filed_by_id="stranger",
                    against_id="bob",
                    description="x",
                )
            )

    def test_raises_when_against_not_participant(self) -> None:
        uow = FakeGuarantorshipUnitOfWork()
        _make_deal(uow)

        with pytest.raises(ValueError):
            FileComplaintUseCase(uow).execute(
                FileComplaintCommand(
                    deal_id="deal-1",
                    filed_by_id="alice",
                    against_id="stranger",
                    description="x",
                )
            )


# ─── CastVote ─────────────────────────────────────────────────────────────────


class TestCastVoteUseCase:
    def _setup(self) -> FakeGuarantorshipUnitOfWork:
        uow = FakeGuarantorshipUnitOfWork()
        _make_deal(uow)
        _make_guarantorship(uow, guarantor_id="g-alice", ward_id="alice")
        _make_guarantorship(uow, guarantor_id="g-bob", ward_id="bob")
        _make_complaint(uow)
        return uow

    def test_single_vote_does_not_resolve(self) -> None:
        uow = self._setup()

        complaint = CastVoteUseCase(uow).execute(
            CastVoteCommand(
                complaint_id="complaint-1",
                voter_id="g-alice",
                vote=Verdict.COMPENSATE_INITIATOR,
            )
        )

        assert complaint.status == ComplaintStatus.VOTING  # not yet resolved
        assert len(complaint.votes) == 1

    def test_unanimous_votes_resolve_complaint(self) -> None:
        uow = self._setup()
        uc = CastVoteUseCase(uow)

        uc.execute(
            CastVoteCommand(
                complaint_id="complaint-1",
                voter_id="g-alice",
                vote=Verdict.COMPENSATE_INITIATOR,
            )
        )
        complaint = uc.execute(
            CastVoteCommand(
                complaint_id="complaint-1",
                voter_id="g-bob",
                vote=Verdict.COMPENSATE_INITIATOR,
            )
        )

        assert complaint.status == ComplaintStatus.RESOLVED
        assert complaint.verdict == Verdict.COMPENSATE_INITIATOR

    def test_raises_when_not_a_guarantor(self) -> None:
        uow = self._setup()

        with pytest.raises(PermissionError, match="guarantor"):
            CastVoteUseCase(uow).execute(
                CastVoteCommand(
                    complaint_id="complaint-1",
                    voter_id="random-person",
                    vote=Verdict.DISMISS,
                )
            )

    def test_raises_when_voting_twice(self) -> None:
        uow = self._setup()
        uc = CastVoteUseCase(uow)
        uc.execute(
            CastVoteCommand(
                complaint_id="complaint-1",
                voter_id="g-alice",
                vote=Verdict.DISMISS,
            )
        )

        with pytest.raises(ValueError, match="already cast"):
            uc.execute(
                CastVoteCommand(
                    complaint_id="complaint-1",
                    voter_id="g-alice",
                    vote=Verdict.DISMISS,
                )
            )


# ─── EscalateComplaint ────────────────────────────────────────────────────────


class TestEscalateComplaintUseCase:
    def test_escalates_after_deadline(self) -> None:
        uow = FakeGuarantorshipUnitOfWork()
        _make_complaint(uow, deadline_past=True)

        complaint = EscalateComplaintUseCase(uow).execute(
            EscalateComplaintCommand(complaint_id="complaint-1")
        )

        assert complaint.status == ComplaintStatus.ESCALATED
        assert complaint.escalation_level == 1
        assert uow.committed

    def test_raises_when_deadline_not_passed(self) -> None:
        uow = FakeGuarantorshipUnitOfWork()
        _make_complaint(uow, deadline_past=False)

        with pytest.raises(ValueError, match="deadline"):
            EscalateComplaintUseCase(uow).execute(
                EscalateComplaintCommand(complaint_id="complaint-1")
            )

    def test_raises_when_max_escalation_reached(self) -> None:
        uow = FakeGuarantorshipUnitOfWork()
        # default escalation_levels = 1, complaint already at level 1
        _make_complaint(uow, escalation_level=1, deadline_past=True)

        with pytest.raises(ValueError, match="Maximum escalation"):
            EscalateComplaintUseCase(uow).execute(
                EscalateComplaintCommand(complaint_id="complaint-1")
            )

    def test_raises_when_not_found(self) -> None:
        uow = FakeGuarantorshipUnitOfWork()

        with pytest.raises(LookupError):
            EscalateComplaintUseCase(uow).execute(
                EscalateComplaintCommand(complaint_id="missing")
            )


# ─── PlatformSettings ─────────────────────────────────────────────────────────


class TestPlatformSettingsUseCases:
    def test_get_returns_defaults(self) -> None:
        uow = FakeGuarantorshipUnitOfWork()
        settings = GetPlatformSettingsUseCase(uow).execute()

        assert settings.required_guarantors_count == 2
        assert settings.guarantor_ward_limit == 5
        assert settings.escalation_levels == 1

    def test_update_required_guarantors_count(self) -> None:
        uow = FakeGuarantorshipUnitOfWork()
        settings = UpdatePlatformSettingsUseCase(uow).execute(
            UpdatePlatformSettingsCommand(required_guarantors_count=3)
        )
        assert settings.required_guarantors_count == 3
        assert uow.committed

    def test_update_partial_fields(self) -> None:
        uow = FakeGuarantorshipUnitOfWork()
        settings = UpdatePlatformSettingsUseCase(uow).execute(
            UpdatePlatformSettingsCommand(guarantor_ward_limit=10)
        )
        assert settings.guarantor_ward_limit == 10
        assert settings.required_guarantors_count == 2  # unchanged

    def test_raises_when_required_guarantors_below_one(self) -> None:
        uow = FakeGuarantorshipUnitOfWork()

        with pytest.raises(ValueError, match="required_guarantors_count"):
            UpdatePlatformSettingsUseCase(uow).execute(
                UpdatePlatformSettingsCommand(required_guarantors_count=0)
            )

    def test_raises_when_ward_limit_below_one(self) -> None:
        uow = FakeGuarantorshipUnitOfWork()

        with pytest.raises(ValueError, match="guarantor_ward_limit"):
            UpdatePlatformSettingsUseCase(uow).execute(
                UpdatePlatformSettingsCommand(guarantor_ward_limit=0)
            )

    def test_raises_when_escalation_levels_negative(self) -> None:
        uow = FakeGuarantorshipUnitOfWork()

        with pytest.raises(ValueError, match="escalation_levels"):
            UpdatePlatformSettingsUseCase(uow).execute(
                UpdatePlatformSettingsCommand(escalation_levels=-1)
            )
