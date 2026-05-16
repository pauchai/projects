"""SQLAlchemy Unit of Work for the Guarantorship bounded context."""

from __future__ import annotations

from sqlalchemy.orm import Session, sessionmaker

from guarantorship.infrastructure.sqlalchemy_repository import (
    SqlAlchemyGuaranteeRequestRepository,
    SqlAlchemyZeroCircleRepository,
)


class SqlAlchemyGuarantorshipUnitOfWork:
    """UnitOfWork backed by a SQLAlchemy Session for the Guarantorship context."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def __enter__(self) -> "SqlAlchemyGuarantorshipUnitOfWork":
        self._session = self._session_factory()
        self.requests = SqlAlchemyGuaranteeRequestRepository(self._session)
        self.circles = SqlAlchemyZeroCircleRepository(self._session)
        return self

    def __exit__(self, exc_type: type[BaseException] | None, *args: object) -> None:
        if exc_type is not None:
            self._session.rollback()
        self._session.close()

    def commit(self) -> None:
        self._session.commit()

    def rollback(self) -> None:
        self._session.rollback()
