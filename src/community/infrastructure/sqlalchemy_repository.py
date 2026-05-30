from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from community.domain.community import Community
from community.domain.community_status import CommunityStatus
from community.domain.feature_request import FeatureRequest
from community.domain.feature_status import FeatureStatus
from community.domain.fund import CommunityFund, FundDistribution, FundTransaction
from community.domain.invite_code import CommunityInviteCode
from community.infrastructure.orm import (
    community_feature_requests_table,
    community_fund_distributions_table,
    community_fund_transactions_table,
    community_funds_table,
    community_invite_codes_table,
    communities_table,
)


class SqlAlchemyCommunityRepository:
    def __init__(self, session: Session, uow: object | None = None) -> None:
        self._session = session
        self._uow = uow

    def find_by_id(self, community_id: str) -> Community | None:
        community = self._session.get(
            Community,
            community_id,
            options=[
                selectinload(Community.memberships),  # type: ignore[attr-defined]
            ],
        )
        if community is None:
            return None
        self._init_transient(community)
        return community

    def save(self, community: Community) -> None:
        events = community.collect_events()
        if events and self._uow is not None and hasattr(self._uow, "collect_events"):
            self._uow.collect_events(events)
        self._session.merge(community)
        self._session.flush()

    def search(
        self,
        owner_id: str | None = None,
        member_user_id: str | None = None,
        status: CommunityStatus | None = None,
        keyword: str | None = None,
    ) -> list[Community]:
        from community.infrastructure.orm import community_memberships_table

        query = select(Community).options(
            selectinload(Community.memberships),  # type: ignore[attr-defined]
        )

        if status is not None:
            query = query.where(communities_table.c.status == status)

        if keyword is not None:
            pattern = f"%{keyword.lower()}%"
            query = query.where(
                communities_table.c.name.ilike(pattern)
                | communities_table.c.description.ilike(pattern)
            )

        if owner_id is not None:
            query = query.where(communities_table.c.owner_id == owner_id)

        if member_user_id is not None:
            member_subq = (
                select(community_memberships_table.c.community_id)
                .where(
                    community_memberships_table.c.user_id == member_user_id,
                    community_memberships_table.c.is_active.is_(True),
                )
                .distinct()
                .subquery()
            )
            query = query.where(
                communities_table.c.community_id.in_(select(member_subq))
            )

        results = self._session.scalars(query).unique().all()
        for c in results:
            self._init_transient(c)
        return list(results)

    @staticmethod
    def _init_transient(community: Community) -> None:
        if not hasattr(community, "_events"):
            community._events = []


class SqlAlchemyFeatureRequestRepository:
    def __init__(self, session: Session, uow: object | None = None) -> None:
        self._session = session
        self._uow = uow

    def find_by_id(self, request_id: str) -> FeatureRequest | None:
        fr = self._session.get(FeatureRequest, request_id)
        if fr is None:
            return None
        self._init_transient(fr)
        return fr

    def save(self, feature_request: FeatureRequest) -> None:
        events = feature_request.collect_events()
        if events and self._uow is not None and hasattr(self._uow, "collect_events"):
            self._uow.collect_events(events)
        self._session.merge(feature_request)
        self._session.flush()

    def find_by_community(self, community_id: str) -> list[FeatureRequest]:
        query = select(FeatureRequest).where(
            community_feature_requests_table.c.community_id == community_id
        )
        results = self._session.scalars(query).all()
        for fr in results:
            self._init_transient(fr)
        return list(results)

    def find_all(
        self,
        community_id: str | None = None,
        status: FeatureStatus | None = None,
        author_id: str | None = None,
    ) -> list[FeatureRequest]:
        query = select(FeatureRequest)

        if community_id is not None:
            query = query.where(
                community_feature_requests_table.c.community_id == community_id
            )
        if status is not None:
            query = query.where(
                community_feature_requests_table.c.status == status
            )
        if author_id is not None:
            query = query.where(
                community_feature_requests_table.c.author_id == author_id
            )

        results = self._session.scalars(query).all()
        for fr in results:
            self._init_transient(fr)
        return list(results)

    @staticmethod
    def _init_transient(feature_request: FeatureRequest) -> None:
        if not hasattr(feature_request, "_events"):
            feature_request._events = []


class SqlAlchemyFundRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def find_by_community(self, community_id: str) -> CommunityFund | None:
        query = select(CommunityFund).where(
            community_funds_table.c.community_id == community_id
        )
        return self._session.scalars(query).first()

    def save(self, fund: CommunityFund) -> None:
        self._session.merge(fund)
        self._session.flush()

    def save_transaction(self, tx: FundTransaction) -> None:
        self._session.merge(tx)
        self._session.flush()

    def save_distribution(self, dist: FundDistribution) -> None:
        self._session.merge(dist)
        self._session.flush()

    def list_transactions(self, fund_id: str) -> list[FundTransaction]:
        query = (
            select(FundTransaction)
            .where(community_fund_transactions_table.c.fund_id == fund_id)
            .order_by(community_fund_transactions_table.c.created_at.desc())
        )
        return list(self._session.scalars(query).all())

    def list_distributions(self, fund_id: str) -> list[FundDistribution]:
        query = (
            select(FundDistribution)
            .where(community_fund_distributions_table.c.fund_id == fund_id)
            .order_by(community_fund_distributions_table.c.created_at.desc())
        )
        return list(self._session.scalars(query).all())


class SqlAlchemyCommunityInviteCodeRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def find_by_code(self, code: str) -> CommunityInviteCode | None:
        query = select(CommunityInviteCode).where(
            community_invite_codes_table.c.code == code.upper().strip()
        )
        return self._session.scalars(query).first()

    def find_by_id(self, code_id: str) -> CommunityInviteCode | None:
        return self._session.get(CommunityInviteCode, code_id)

    def find_by_community(self, community_id: str) -> list[CommunityInviteCode]:
        query = (
            select(CommunityInviteCode)
            .where(community_invite_codes_table.c.community_id == community_id)
            .order_by(community_invite_codes_table.c.created_at.desc())
        )
        return list(self._session.scalars(query).all())

    def save(self, invite_code: CommunityInviteCode) -> None:
        self._session.merge(invite_code)
        self._session.flush()

    def delete(self, code_id: str) -> None:
        code = self.find_by_id(code_id)
        if code is not None:
            self._session.delete(code)
            self._session.flush()
