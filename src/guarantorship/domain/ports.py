"""Domain ports (driven interfaces) for the Guarantorship bounded context."""

from __future__ import annotations

from typing import Protocol

from guarantorship.domain.guarantee_request import GuaranteeRequest
from guarantorship.domain.zero_circle import ZeroCircle


class GuaranteeRequestRepository(Protocol):
    """Storage port for GuaranteeRequest aggregates."""

    def save(self, request: GuaranteeRequest) -> None: ...

    def find_by_id(self, request_id: str) -> GuaranteeRequest | None: ...

    def find_incoming(self, guarantor_id: str) -> list[GuaranteeRequest]: ...
    """Requests where I am the intended guarantor."""

    def find_outgoing(self, ward_id: str) -> list[GuaranteeRequest]: ...
    """Requests I submitted as a ward."""

    def find_active_guarantors_for(self, ward_id: str) -> list[str]: ...
    """Return guarantor_ids whose requests were accepted for this ward."""


class ZeroCircleRepository(Protocol):
    """Storage port for ZeroCircle aggregates."""

    def save(self, circle: ZeroCircle) -> None: ...

    def find_by_id(self, circle_id: str) -> ZeroCircle | None: ...

    def find_open(self) -> list[ZeroCircle]: ...
    """Return all circles with status='open'."""

    def find_active_circle_for_user(self, user_id: str) -> ZeroCircle | None: ...
    """Return the open circle the user is currently a member of, if any."""


class GuarantorshipUnitOfWork(Protocol):
    """Unit of Work for the Guarantorship context."""

    requests: GuaranteeRequestRepository
    circles: ZeroCircleRepository

    def __enter__(self) -> "GuarantorshipUnitOfWork": ...
    def __exit__(self, *args: object) -> None: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...
