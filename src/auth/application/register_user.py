"""RegisterUser use case — creates a new user with local credentials."""

import uuid

from auth.domain.ports import PasswordHasher, UnitOfWork
from auth.domain.user import Credential, User


class RegisterUserUseCase:
    """Registers a new user with email/password (local provider).

    Creates a User aggregate, hashes the password, attaches a local Credential,
    and persists atomically via UnitOfWork.
    """

    def __init__(self, uow: UnitOfWork, password_hasher: PasswordHasher) -> None:
        self._uow = uow
        self._password_hasher = password_hasher

    def execute(
        self,
        user_id: str,
        email: str,
        password: str,
        display_name: str,
    ) -> str:
        """Register a new user. Returns user_id. Raises ValueError if email is taken."""
        with self._uow as uow:
            existing = uow.users.find_by_email(email)
            if existing is not None:
                raise ValueError("Email already registered")

            user = User(user_id=user_id, email=email, display_name=display_name)

            hashed = self._password_hasher.hash(password)
            credential = Credential(
                credential_id=str(uuid.uuid4()),
                user_id=user_id,
                provider="local",
                provider_user_id=user.email,  # normalized email
                hashed_secret=hashed,
            )
            user.add_credential(credential)

            uow.users.save(user)
            uow.commit()
            return user.user_id
