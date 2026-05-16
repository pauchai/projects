"""Fake implementations of GuarantorshipUnitOfWork for unit tests."""

from __future__ import annotations

from guarantorship.domain.guarantee_request import GuaranteeRequest
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
