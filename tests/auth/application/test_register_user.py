"""Tests for RegisterUser use case."""

import pytest

from auth.application.register_user import RegisterUserUseCase
from tests.auth.fakes.fake_unit_of_work import (
    FakeUnitOfWork,
    FakePasswordHasher,
)


class TestRegisterUserUseCase:
    """RegisterUser creates a new user with local credentials."""

    def test_creates_user_with_given_fields(self) -> None:
        uow = FakeUnitOfWork()
        hasher = FakePasswordHasher()
        use_case = RegisterUserUseCase(uow=uow, password_hasher=hasher)

        user_id = use_case.execute(
            user_id="u1",
            email="alice@example.com",
            password="secret123",
            display_name="Alice",
        )

        assert user_id == "u1"
        user = uow.users.find_by_id("u1")
        assert user is not None
        assert user.email == "alice@example.com"
        assert user.display_name == "Alice"

    def test_hashes_password_and_stores_local_credential(self) -> None:
        uow = FakeUnitOfWork()
        hasher = FakePasswordHasher()
        use_case = RegisterUserUseCase(uow=uow, password_hasher=hasher)

        use_case.execute(
            user_id="u1",
            email="alice@example.com",
            password="secret123",
            display_name="Alice",
        )

        user = uow.users.find_by_id("u1")
        assert user is not None
        cred = user.find_credential_by_provider("local")
        assert cred is not None
        assert cred.hashed_secret == "hashed:secret123"
        assert cred.provider_user_id == "u1"  # user_id; email lives on User entity

    def test_commits_transaction(self) -> None:
        uow = FakeUnitOfWork()
        hasher = FakePasswordHasher()
        use_case = RegisterUserUseCase(uow=uow, password_hasher=hasher)

        use_case.execute(
            user_id="u1",
            email="alice@example.com",
            password="secret123",
            display_name="Alice",
        )

        assert uow.committed is True

    def test_raises_when_email_already_registered(self) -> None:
        uow = FakeUnitOfWork()
        hasher = FakePasswordHasher()
        use_case = RegisterUserUseCase(uow=uow, password_hasher=hasher)

        use_case.execute(
            user_id="u1",
            email="alice@example.com",
            password="secret123",
            display_name="Alice",
        )

        with pytest.raises(ValueError, match="Email already registered"):
            use_case.execute(
                user_id="u2",
                email="alice@example.com",
                password="other_pass",
                display_name="Alice Again",
            )

    def test_user_is_active_after_registration(self) -> None:
        uow = FakeUnitOfWork()
        hasher = FakePasswordHasher()
        use_case = RegisterUserUseCase(uow=uow, password_hasher=hasher)

        use_case.execute(
            user_id="u1",
            email="alice@example.com",
            password="secret123",
            display_name="Alice",
        )

        user = uow.users.find_by_id("u1")
        assert user is not None
        assert user.is_active is True

    def test_email_case_insensitive_duplicate_detection(self) -> None:
        uow = FakeUnitOfWork()
        hasher = FakePasswordHasher()
        use_case = RegisterUserUseCase(uow=uow, password_hasher=hasher)

        use_case.execute(
            user_id="u1",
            email="Alice@Example.COM",
            password="secret123",
            display_name="Alice",
        )

        with pytest.raises(ValueError, match="Email already registered"):
            use_case.execute(
                user_id="u2",
                email="alice@example.com",
                password="other_pass",
                display_name="Alice Again",
            )
