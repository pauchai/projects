"""SQLAlchemy repository implementations for the Guarantorship context."""

from __future__ import annotations

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from guarantorship.domain.guarantee_request import GuaranteeRequest, GuaranteeRequestStatus
from guarantorship.domain.zero_circle import ZeroCircle, ZeroCircleStatus


class SqlAlchemyGuaranteeRequestRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, request: GuaranteeRequest) -> None:
        self._session.merge(request)
        self._session.flush()

    def find_by_id(self, request_id: str) -> GuaranteeRequest | None:
        return self._session.get(GuaranteeRequest, request_id)

    def find_incoming(self, guarantor_id: str) -> list[GuaranteeRequest]:
        result = self._session.execute(
            select(GuaranteeRequest).where(
                GuaranteeRequest.guarantor_id == guarantor_id
            ).order_by(GuaranteeRequest.created_at.desc())
        )
        return list(result.scalars().all())

    def find_outgoing(self, ward_id: str) -> list[GuaranteeRequest]:
        result = self._session.execute(
            select(GuaranteeRequest).where(
                GuaranteeRequest.ward_id == ward_id
            ).order_by(GuaranteeRequest.created_at.desc())
        )
        return list(result.scalars().all())

    def find_active_guarantors_for(self, ward_id: str) -> list[str]:
        result = self._session.execute(
            select(GuaranteeRequest.guarantor_id).where(
                GuaranteeRequest.ward_id == ward_id,
                GuaranteeRequest.status == GuaranteeRequestStatus.ACCEPTED.value,
            )
        )
        return list(result.scalars().all())


class SqlAlchemyZeroCircleRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, circle: ZeroCircle) -> None:
        self._session.merge(circle)
        self._session.flush()

    def find_by_id(self, circle_id: str) -> ZeroCircle | None:
        return self._session.get(ZeroCircle, circle_id)

    def find_open(self) -> list[ZeroCircle]:
        result = self._session.execute(
            select(ZeroCircle).where(
                ZeroCircle.status == ZeroCircleStatus.OPEN.value
            ).order_by(ZeroCircle.created_at.desc())
        )
        return list(result.scalars().all())

    def find_active_circle_for_user(self, user_id: str) -> ZeroCircle | None:
        stmt = text(
            "SELECT zc.circle_id FROM zero_circles zc "
            "JOIN zero_circle_members zcm ON zc.circle_id = zcm.circle_id "
            "WHERE zcm.user_id = :user_id AND zc.status = 'open' "
            "LIMIT 1"
        )
        row = self._session.execute(stmt, {"user_id": user_id}).fetchone()
        if row is None:
            return None
        return self.find_by_id(row[0])
