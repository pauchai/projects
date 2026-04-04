"""Authenticate use case — verifies credentials and returns a JWT token."""

from auth.domain.ports import PasswordHasher, TokenService, UnitOfWork


class AuthenticateUseCase:
    """Authenticates a user with email/password and returns an access token.

    Looks up the user by email, verifies the local credential's password,
    and delegates token creation to the TokenService port.
    """

    def __init__(
        self,
        uow: UnitOfWork,
        password_hasher: PasswordHasher,
        token_service: TokenService,
    ) -> None:
        self._uow = uow
        self._password_hasher = password_hasher
        self._token_service = token_service

    def execute(self, email: str, password: str) -> str:
        """Authenticate and return an access token.

        Raises ValueError if credentials are invalid or user is inactive.
        """
        normalized_email = email.strip().lower()

        with self._uow as uow:
            user = uow.users.find_by_email(normalized_email)
            if user is None:
                raise ValueError("Invalid email or password")

            if not user.is_active:
                raise ValueError("User account is inactive")

            local_credential = user.find_credential_by_provider("local")
            if local_credential is None or local_credential.hashed_secret is None:
                raise ValueError("Invalid email or password")

            if not self._password_hasher.verify(
                password, local_credential.hashed_secret
            ):
                raise ValueError("Invalid email or password")

            return self._token_service.create_access_token(user.user_id)
