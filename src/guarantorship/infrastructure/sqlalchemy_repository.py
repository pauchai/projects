"""SQLAlchemy repository implementations for the Guarantorship context."""

from __future__ import annotations

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from guarantorship.domain.complaint import Complaint
from guarantorship.domain.deal import Deal
from guarantorship.domain.guarantee_request import GuaranteeRequest, GuaranteeRequestStatus
from guarantorship.domain.guarantorship import Guarantorship
from guarantorship.domain.platform_settings import PlatformSettings
from guarantorship.domain.user_deposit import UserDeposit
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
            select(GuaranteeRequest)
            .where(GuaranteeRequest.guarantor_id == guarantor_id)
            .order_by(GuaranteeRequest.created_at.desc())
        )
        return list(result.scalars().all())

    def find_outgoing(self, ward_id: str) -> list[GuaranteeRequest]:
        result = self._session.execute(
            select(GuaranteeRequest)
            .where(GuaranteeRequest.ward_id == ward_id)
            .order_by(GuaranteeRequest.created_at.desc())
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


class SqlAlchemyGuarantorshipRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, guarantorship: Guarantorship) -> None:
        self._session.merge(guarantorship)
        self._session.flush()

    def find_by_id(self, guarantorship_id: str) -> Guarantorship | None:
        return self._session.get(Guarantorship, guarantorship_id)

    def find_by_ward(self, ward_id: str) -> list[Guarantorship]:
        result = self._session.execute(
            select(Guarantorship)
            .where(Guarantorship.ward_id == ward_id)
            .order_by(Guarantorship.created_at.desc())
        )
        return list(result.scalars().all())

    def find_by_guarantor(self, guarantor_id: str) -> list[Guarantorship]:
        result = self._session.execute(
            select(Guarantorship)
            .where(Guarantorship.guarantor_id == guarantor_id)
            .order_by(Guarantorship.created_at.desc())
        )
        return list(result.scalars().all())

    def count_wards_for_guarantor(self, guarantor_id: str) -> int:
        result = self._session.execute(
            select(Guarantorship).where(Guarantorship.guarantor_id == guarantor_id)
        )
        return len(result.scalars().all())


class SqlAlchemyUserDepositRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, deposit: UserDeposit) -> None:
        self._session.merge(deposit)
        self._session.flush()

    def find_by_id(self, deposit_id: str) -> UserDeposit | None:
        return self._session.get(UserDeposit, deposit_id)

    def find_by_ward(self, ward_id: str) -> list[UserDeposit]:
        result = self._session.execute(
            select(UserDeposit)
            .where(UserDeposit.ward_id == ward_id)
            .order_by(UserDeposit.created_at.desc())
        )
        return list(result.scalars().all())

    def find_by_guarantor(self, guarantor_id: str) -> list[UserDeposit]:
        result = self._session.execute(
            select(UserDeposit)
            .where(UserDeposit.guarantor_id == guarantor_id)
            .order_by(UserDeposit.created_at.desc())
        )
        return list(result.scalars().all())

    def find_by_ward_and_guarantor(
        self, ward_id: str, guarantor_id: str
    ) -> UserDeposit | None:
        result = self._session.execute(
            select(UserDeposit).where(
                UserDeposit.ward_id == ward_id,
                UserDeposit.guarantor_id == guarantor_id,
            )
        )
        return result.scalars().first()


class SqlAlchemyPlatformSettingsRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self) -> PlatformSettings:
        settings = self._session.get(PlatformSettings, 1)
        if settings is None:
            # seed default if missing (should not happen after migration)
            settings = PlatformSettings(
                id=1,
                required_guarantors_count=2,
                guarantor_ward_limit=5,
                escalation_levels=1,
            )
            self._session.add(settings)
            self._session.flush()
        return settings

    def save(self, settings: PlatformSettings) -> None:
        self._session.merge(settings)
        self._session.flush()


class SqlAlchemyDealRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, deal: Deal) -> None:
        self._session.merge(deal)
        self._session.flush()

    def find_by_id(self, deal_id: str) -> Deal | None:
        return self._session.get(Deal, deal_id)

    def find_by_participant(self, user_id: str) -> list[Deal]:
        result = self._session.execute(
            select(Deal).where(
                (Deal.initiator_id == user_id) | (Deal.counterparty_id == user_id)
            ).order_by(Deal.created_at.desc())
        )
        return list(result.scalars().all())


class SqlAlchemyComplaintRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, complaint: Complaint) -> None:
        self._session.merge(complaint)
        self._session.flush()

    def find_by_id(self, complaint_id: str) -> Complaint | None:
        return self._session.get(Complaint, complaint_id)

    def find_by_deal(self, deal_id: str) -> list[Complaint]:
        result = self._session.execute(
            select(Complaint)
            .where(Complaint.deal_id == deal_id)
            .order_by(Complaint.created_at.desc())
        )
        return list(result.scalars().all())

    def find_open_for_voter(self, voter_id: str) -> list[Complaint]:
        """Return complaints in voting/escalated state where voter is a guarantor.

        For simplicity we return all active complaints and let the caller filter.
        A proper implementation would join with guarantorships.
        """
        result = self._session.execute(
            select(Complaint).where(
                Complaint.status.in_(["voting", "escalated"])
            ).order_by(Complaint.created_at.desc())
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
            select(ZeroCircle)
            .where(ZeroCircle.status == ZeroCircleStatus.OPEN.value)
            .order_by(ZeroCircle.created_at.desc())
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
