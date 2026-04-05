"""SQLAlchemy implementation of UnitOfWork for the Auth bounded context."""

from sqlalchemy.orm import Session, sessionmaker

from auth.infrastructure.sqlalchemy_repository import SqlAlchemyUserRepository


class SqlAlchemyUnitOfWork:
    """UnitOfWork backed by a SQLAlchemy Session.

    Implements the UnitOfWork Protocol defined in ``auth.domain.ports``.
    Application Services manage the lifecycle: ``with uow: ... uow.commit()``.
    """

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def __enter__(self) -> "SqlAlchemyUnitOfWork":
        self._session = self._session_factory()
        self.users = SqlAlchemyUserRepository(self._session)
        return self

    def __exit__(self, exc_type: type[BaseException] | None, *args: object) -> None:
        if exc_type is not None:
            self._session.rollback()
        self._session.close()

    def commit(self) -> None:
        self._session.commit()

    def rollback(self) -> None:
        self._session.rollback()
