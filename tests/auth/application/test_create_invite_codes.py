"""Tests for CreateInviteCodesUseCase."""

from __future__ import annotations

import pytest

from auth.application.create_invite_codes import CreateInviteCodesUseCase
from tests.auth.fakes.fake_unit_of_work import FakeUnitOfWork


class TestCreateInviteCodesUseCase:
    def test_returns_requested_number_of_codes(self) -> None:
        uow = FakeUnitOfWork()
        use_case = CreateInviteCodesUseCase(uow)

        codes = use_case.execute(admin_user_id="admin-1", count=5)

        assert len(codes) == 5

    def test_each_code_has_unique_value(self) -> None:
        uow = FakeUnitOfWork()
        use_case = CreateInviteCodesUseCase(uow)

        codes = use_case.execute(admin_user_id="admin-1", count=10)

        code_strings = [c.code for c in codes]
        assert len(set(code_strings)) == 10

    def test_codes_are_issued_by_admin(self) -> None:
        uow = FakeUnitOfWork()
        use_case = CreateInviteCodesUseCase(uow)

        codes = use_case.execute(admin_user_id="admin-42", count=3)

        assert all(c.issued_by == "admin-42" for c in codes)

    def test_codes_are_single_use_by_default(self) -> None:
        uow = FakeUnitOfWork()
        use_case = CreateInviteCodesUseCase(uow)

        codes = use_case.execute(admin_user_id="admin-1", count=2)

        assert all(c.max_uses == 1 for c in codes)
        assert all(c.uses_left == 1 for c in codes)

    def test_codes_respect_custom_max_uses(self) -> None:
        uow = FakeUnitOfWork()
        use_case = CreateInviteCodesUseCase(uow)

        codes = use_case.execute(admin_user_id="admin-1", count=2, max_uses=5)

        assert all(c.max_uses == 5 for c in codes)

    def test_codes_are_active_on_creation(self) -> None:
        uow = FakeUnitOfWork()
        use_case = CreateInviteCodesUseCase(uow)

        codes = use_case.execute(admin_user_id="admin-1", count=3)

        assert all(c.is_active for c in codes)

    def test_commits_transaction(self) -> None:
        uow = FakeUnitOfWork()
        use_case = CreateInviteCodesUseCase(uow)

        use_case.execute(admin_user_id="admin-1", count=1)

        assert uow.committed is True

    def test_codes_are_persisted_in_repository(self) -> None:
        uow = FakeUnitOfWork()
        use_case = CreateInviteCodesUseCase(uow)

        codes = use_case.execute(admin_user_id="admin-1", count=3)

        for code in codes:
            found = uow.invite_codes.find_by_code(code.code)
            assert found is not None
            assert found.code_id == code.code_id

    def test_raises_when_count_is_zero(self) -> None:
        uow = FakeUnitOfWork()
        use_case = CreateInviteCodesUseCase(uow)

        with pytest.raises(ValueError, match="count must be between"):
            use_case.execute(admin_user_id="admin-1", count=0)

    def test_raises_when_count_exceeds_500(self) -> None:
        uow = FakeUnitOfWork()
        use_case = CreateInviteCodesUseCase(uow)

        with pytest.raises(ValueError, match="count must be between"):
            use_case.execute(admin_user_id="admin-1", count=501)

    def test_raises_when_max_uses_is_zero(self) -> None:
        uow = FakeUnitOfWork()
        use_case = CreateInviteCodesUseCase(uow)

        with pytest.raises(ValueError, match="max_uses must be at least 1"):
            use_case.execute(admin_user_id="admin-1", count=1, max_uses=0)
