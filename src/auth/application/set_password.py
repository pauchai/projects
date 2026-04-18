"""Set password for an existing user who doesn't have local credentials."""

from auth.domain.ports import PasswordHasher
from auth.domain.user import Credential, User


class SetPasswordUseCase:
    """Sets a local (email+password) credential for a user.

    The user must NOT already have a local credential.
    Creates and attaches a new Credential with a hashed password.
    """

    def __init__(self, uow, password_hasher: PasswordHasher) -> None:
        self._uow = uow
        self._password_hasher = password_hasher

    def execute(self, user_id: str, password: str) -> None:
        """Set password for user.

        Raises:
            LookupError: If user doesn't exist.
            ValueError: If user already has local credentials.
        """
        with self._uow:
            user = self._uow.users.find_by_id(user_id)
            if user is None:
                raise LookupError(f"User {user_id} not found")

            if user.has_credential_for_provider("local"):
                raise ValueError("User already has local credentials")

            import uuid

            credential = Credential(
                credential_id=str(uuid.uuid4()),
                user_id=user_id,
                provider="local",
                provider_user_id=user.email,  # email as provider_user_id for local
                hashed_secret=self._password_hasher.hash(password),
            )
            user.add_credential(credential)
            self._uow.users.save(user)
            self._uow.commit()
