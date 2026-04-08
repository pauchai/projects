"""Tests for ListFeatureRequests use case."""

from project_collaboration.domain.feature_status import FeatureStatus
from tests.project_collaboration.fakes.fake_unit_of_work import FakeUnitOfWork
from tests.project_collaboration.factories import (
    make_feature_request,
    make_planned_feature_request,
    save_feature_request,
)


class TestListFeatureRequestsUseCase:
    """ListFeatureRequests returns feature requests with optional filters."""

    def test_returns_all_feature_requests(self) -> None:
        from project_collaboration.application.list_feature_requests import (
            ListFeatureRequestsUseCase,
        )

        uow = FakeUnitOfWork()
        save_feature_request(uow, make_feature_request(request_id="fr1"))
        save_feature_request(uow, make_feature_request(request_id="fr2"))
        use_case = ListFeatureRequestsUseCase(uow=uow)

        result = use_case.execute()

        assert len(result) == 2

    def test_returns_empty_when_no_requests(self) -> None:
        from project_collaboration.application.list_feature_requests import (
            ListFeatureRequestsUseCase,
        )

        uow = FakeUnitOfWork()
        use_case = ListFeatureRequestsUseCase(uow=uow)

        result = use_case.execute()

        assert result == []

    def test_filters_by_status(self) -> None:
        from project_collaboration.application.list_feature_requests import (
            ListFeatureRequestsUseCase,
        )

        uow = FakeUnitOfWork()
        save_feature_request(uow, make_feature_request(request_id="fr1"))
        save_feature_request(uow, make_planned_feature_request(request_id="fr2"))
        use_case = ListFeatureRequestsUseCase(uow=uow)

        result = use_case.execute(status=FeatureStatus.PLANNED)

        assert len(result) == 1
        assert result[0].request_id == "fr2"

    def test_filters_by_author_id(self) -> None:
        from project_collaboration.application.list_feature_requests import (
            ListFeatureRequestsUseCase,
        )

        uow = FakeUnitOfWork()
        save_feature_request(
            uow, make_feature_request(request_id="fr1", author_id="alice")
        )
        save_feature_request(
            uow, make_feature_request(request_id="fr2", author_id="bob")
        )
        use_case = ListFeatureRequestsUseCase(uow=uow)

        result = use_case.execute(author_id="alice")

        assert len(result) == 1
        assert result[0].author_id == "alice"
