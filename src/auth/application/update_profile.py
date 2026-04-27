"""Update mutable profile fields (email, display_name) for an existing user."""

from dataclasses import dataclass


@dataclass(frozen=True)
class UpdatedProfile:
    """Snapshot of the user's profile fields after a successful update."""

    user_id: str
    email: str
    display_name: str


class UpdateProfileUseCase:
    """Update a user's email and/or display_name.

    Enforces email uniqueness: raises ValueError if the new email is already
    registered to a *different* user.

    Neither field is required — omitting both is a valid no-op.

    # TODO: when email is changed, trigger an email-verification flow
    #       (send confirmation link) and mark the new address as unverified
    #       until the user clicks through.
    """

    def __init__(self, uow) -> None:
        self._uow = uow

    def execute(
        self,
        user_id: str,
        *,
        email: str | None = None,
        display_name: str | None = None,
    ) -> UpdatedProfile:
        """Update profile fields for *user_id*.

        Args:
            user_id: ID of the user to update.
            email: New email address (optional). Normalized to lowercase.
            display_name: New display name (optional).

        Returns:
            UpdatedProfile with the final email and display_name values.

        Raises:
            LookupError: If the user does not exist.
            ValueError: If *email* is already registered to another user,
                        or if domain validation fails (empty, missing @, etc.).
        """
        with self._uow:
            user = self._uow.users.find_by_id(user_id)
            if user is None:
                raise LookupError(f"User {user_id} not found")

            if email is not None:
                normalized = email.strip().lower()
                existing = self._uow.users.find_by_email(normalized)
                if existing is not None and existing.user_id != user_id:
                    raise ValueError("Email already registered")

            user.update_profile(email=email, display_name=display_name)
            self._uow.users.save(user)
            self._uow.commit()
            return UpdatedProfile(
                user_id=user.user_id,
                email=user.email,
                display_name=user.display_name,
            )
