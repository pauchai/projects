"""Fake implementations of GuarantorshipUnitOfWork for unit tests."""

from __future__ import annotations

from guarantorship.domain.complaint import Complaint
from guarantorship.domain.deal import Deal
from guarantorship.domain.guarantee_request import GuaranteeRequest
from guarantorship.domain.guarantorship import Guarantorship
from guarantorship.domain.platform_settings import PlatformSettings
from guarantorship.domain.user_deposit import UserDeposit
from guarantorship.domain.zero_circle import ZeroCircle, ZeroCircleStatus


class FakeGuaranteeRequestRepository:
    def __init__(self) -> None:
        self._store: dict[str, GuaranteeRequest] = {}

    def save(self, request: GuaranteeRequest) -> None:
        self._store[request.request_id] = request

    def find_by_id(self, request_id: str) -> GuaranteeRequest | None:
        return self._store.get(request_id)

    def find_incoming(self, guarantor_id: str) -> list[GuaranteeRequest]:
        return [r for r in self._store.values() if r.guarantor_id == guarantor_id]

    def find_outgoing(self, ward_id: str) -> list[GuaranteeRequest]:
        return [r for r in self._store.values() if r.ward_id == ward_id]

    def find_active_guarantors_for(self, ward_id: str) -> list[str]:
        from guarantorship.domain.guarantee_request import GuaranteeRequestStatus

        return [
            r.guarantor_id
            for r in self._store.values()
            if r.ward_id == ward_id and r.status == GuaranteeRequestStatus.ACCEPTED
        ]


class FakeGuarantorshipRepository:
    def __init__(self) -> None:
        self._store: dict[str, Guarantorship] = {}

    def save(self, guarantorship: Guarantorship) -> None:
        self._store[guarantorship.guarantorship_id] = guarantorship

    def find_by_id(self, guarantorship_id: str) -> Guarantorship | None:
        return self._store.get(guarantorship_id)

    def find_by_ward(self, ward_id: str) -> list[Guarantorship]:
        return [g for g in self._store.values() if g.ward_id == ward_id]

    def find_by_guarantor(self, guarantor_id: str) -> list[Guarantorship]:
        return [g for g in self._store.values() if g.guarantor_id == guarantor_id]

    def count_wards_for_guarantor(self, guarantor_id: str) -> int:
        return len([g for g in self._store.values() if g.guarantor_id == guarantor_id])


class FakeUserDepositRepository:
    def __init__(self) -> None:
        self._store: dict[str, UserDeposit] = {}

    def save(self, deposit: UserDeposit) -> None:
        self._store[deposit.deposit_id] = deposit

    def find_by_id(self, deposit_id: str) -> UserDeposit | None:
        return self._store.get(deposit_id)

    def find_by_ward(self, ward_id: str) -> list[UserDeposit]:
        return [d for d in self._store.values() if d.ward_id == ward_id]

    def find_by_guarantor(self, guarantor_id: str) -> list[UserDeposit]:
        return [d for d in self._store.values() if d.guarantor_id == guarantor_id]

    def find_by_ward_and_guarantor(
        self, ward_id: str, guarantor_id: str
    ) -> UserDeposit | None:
        for d in self._store.values():
            if d.ward_id == ward_id and d.guarantor_id == guarantor_id:
                return d
        return None


class FakeDealRepository:
    def __init__(self) -> None:
        self._store: dict[str, Deal] = {}

    def save(self, deal: Deal) -> None:
        self._store[deal.deal_id] = deal

    def find_by_id(self, deal_id: str) -> Deal | None:
        return self._store.get(deal_id)

    def find_by_participant(self, user_id: str) -> list[Deal]:
        return [
            d
            for d in self._store.values()
            if d.initiator_id == user_id or d.counterparty_id == user_id
        ]


class FakeComplaintRepository:
    def __init__(self) -> None:
        self._store: dict[str, Complaint] = {}

    def save(self, complaint: Complaint) -> None:
        self._store[complaint.complaint_id] = complaint

    def find_by_id(self, complaint_id: str) -> Complaint | None:
        return self._store.get(complaint_id)

    def find_by_deal(self, deal_id: str) -> list[Complaint]:
        return [c for c in self._store.values() if c.deal_id == deal_id]

    def find_open_for_voter(self, voter_id: str) -> list[Complaint]:
        from guarantorship.domain.complaint import ComplaintStatus

        return [
            c
            for c in self._store.values()
            if c.status in (ComplaintStatus.VOTING, ComplaintStatus.ESCALATED)
        ]


class FakePlatformSettingsRepository:
    def __init__(self) -> None:
        self._settings = PlatformSettings(
            id=1,
            required_guarantors_count=2,
            guarantor_ward_limit=5,
            escalation_levels=1,
        )

    def get(self) -> PlatformSettings:
        return self._settings

    def save(self, settings: PlatformSettings) -> None:
        self._settings = settings


class FakeZeroCircleRepository:
    def __init__(self) -> None:
        self._store: dict[str, ZeroCircle] = {}

    def save(self, circle: ZeroCircle) -> None:
        self._store[circle.circle_id] = circle

    def find_by_id(self, circle_id: str) -> ZeroCircle | None:
        return self._store.get(circle_id)

    def find_open(self) -> list[ZeroCircle]:
        return [c for c in self._store.values() if c.status == ZeroCircleStatus.OPEN]

    def find_active_circle_for_user(self, user_id: str) -> ZeroCircle | None:
        for circle in self._store.values():
            if circle.status == ZeroCircleStatus.OPEN and user_id in circle.member_ids():
                return circle
        return None


class FakeGuarantorshipUnitOfWork:
    def __init__(self) -> None:
        self.requests = FakeGuaranteeRequestRepository()
        self.guarantorships = FakeGuarantorshipRepository()
        self.deposits = FakeUserDepositRepository()
        self.deals = FakeDealRepository()
        self.complaints = FakeComplaintRepository()
        self.settings = FakePlatformSettingsRepository()
        self.circles = FakeZeroCircleRepository()
        self.committed = False

    def __enter__(self) -> "FakeGuarantorshipUnitOfWork":
        return self

    def __exit__(self, *args: object) -> None:
        pass

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        pass
