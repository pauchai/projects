"""SQLAlchemy Unit of Work for the Schedule bounded context."""

from __future__ import annotations

from sqlalchemy.orm import Session, sessionmaker

from schedule.infrastructure.sqlalchemy_repositories import (
    SqlAlchemyAppointmentRepository,
    SqlAlchemyConsultationOfferRepository,
    SqlAlchemyConsultationRequestRepository,
    SqlAlchemyCuratorRepository,
)


class SqlAlchemyScheduleUnitOfWork:
    """UnitOfWork backed by a SQLAlchemy Session for the Schedule context."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def __enter__(self) -> "SqlAlchemyScheduleUnitOfWork":
        self._session = self._session_factory()
        self.curators = SqlAlchemyCuratorRepository(self._session)
        self.requests = SqlAlchemyConsultationRequestRepository(self._session)
        self.offers = SqlAlchemyConsultationOfferRepository(self._session)
        self.appointments = SqlAlchemyAppointmentRepository(self._session)
        return self

    def __exit__(self, exc_type: type[BaseException] | None, *args: object) -> None:
        if exc_type is not None:
            self._session.rollback()
        self._session.close()

    def commit(self) -> None:
        self._session.commit()

    def rollback(self) -> None:
        self._session.rollback()
