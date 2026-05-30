"""SQLAlchemy Unit of Work for the Guarantorship context."""

from __future__ import annotations

from sqlalchemy.orm import Session

from guarantorship.infrastructure.sqlalchemy_repository import (
    SqlAlchemyComplaintRepository,
    SqlAlchemyDealRepository,
    SqlAlchemyGuaranteeRequestRepository,
    SqlAlchemyGuarantorshipRepository,
    SqlAlchemyPlatformSettingsRepository,
    SqlAlchemyUserDepositRepository,
    SqlAlchemyZeroCircleRepository,
)


class SqlAlchemyGuarantorshipUnitOfWork:
    def __init__(self, session_factory: object) -> None:
        self._session_factory = session_factory

    def __enter__(self) -> "SqlAlchemyGuarantorshipUnitOfWork":
        from guarantorship.infrastructure.orm import register_mappers
        register_mappers()
        self._session: Session = self._session_factory()
        self.requests = SqlAlchemyGuaranteeRequestRepository(self._session)
        self.guarantorships = SqlAlchemyGuarantorshipRepository(self._session)
        self.deposits = SqlAlchemyUserDepositRepository(self._session)
        self.settings = SqlAlchemyPlatformSettingsRepository(self._session)
        self.deals = SqlAlchemyDealRepository(self._session)
        self.complaints = SqlAlchemyComplaintRepository(self._session)
        self.circles = SqlAlchemyZeroCircleRepository(self._session)
        return self

    def __exit__(self, *args: object) -> None:
        self.rollback()
        self._session.close()

    def commit(self) -> None:
        self._session.commit()

    def rollback(self) -> None:
        self._session.rollback()
