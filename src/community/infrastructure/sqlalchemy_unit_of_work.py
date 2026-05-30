from sqlalchemy.orm import Session, sessionmaker

from shared_kernel.events import DomainEvent, EventBus


class SqlAlchemyCommunityUnitOfWork:
    def __init__(
        self,
        session_factory: sessionmaker[Session],
        event_bus: EventBus | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._event_bus = event_bus
        self._pending_events: list[DomainEvent] = []

    def __enter__(self) -> "SqlAlchemyCommunityUnitOfWork":
        self._session = self._session_factory()
        self.communities = _import_community_repo(self._session, self)
        self.feature_requests = _import_feature_request_repo(self._session, self)
        self.fund = _import_fund_repo(self._session)
        self.invite_codes = _import_invite_code_repo(self._session)
        return self

    def __exit__(self, exc_type: type[BaseException] | None, *args: object) -> None:
        if exc_type is not None:
            self._session.rollback()
            self._pending_events.clear()
        self._session.close()

    def commit(self) -> None:
        self._session.commit()
        if self._event_bus and self._pending_events:
            self._event_bus.publish(self._pending_events)
        self._pending_events.clear()

    def rollback(self) -> None:
        self._session.rollback()
        self._pending_events.clear()

    def collect_events(self, events: list[DomainEvent]) -> None:
        self._pending_events.extend(events)


def _import_community_repo(session: Session, uow: object):
    from community.infrastructure.sqlalchemy_repository import (
        SqlAlchemyCommunityRepository,
    )
    return SqlAlchemyCommunityRepository(session, uow)


def _import_feature_request_repo(session: Session, uow: object):
    from community.infrastructure.sqlalchemy_repository import (
        SqlAlchemyFeatureRequestRepository,
    )
    return SqlAlchemyFeatureRequestRepository(session, uow)


def _import_fund_repo(session: Session):
    from community.infrastructure.sqlalchemy_repository import (
        SqlAlchemyFundRepository,
    )
    return SqlAlchemyFundRepository(session)


def _import_invite_code_repo(session: Session):
    from community.infrastructure.sqlalchemy_repository import (
        SqlAlchemyCommunityInviteCodeRepository,
    )
    return SqlAlchemyCommunityInviteCodeRepository(session)
