"""Auth domain entities: User aggregate root and Credential entity."""

from dataclasses import dataclass
from datetime import datetime, timezone

# Display names for known auth providers.
_PROVIDER_DISPLAY_NAMES: dict[str, str] = {
    "local": "Email & Password",
    "google": "Google",
    "telegram": "Telegram",
}


@dataclass(frozen=True)
class CredentialSummary:
    """Read-only value object for displaying a credential in the UI.

    Contains only the data needed for presentation — no secrets,
    no mutable state. ``is_removable`` reflects the current business
    rules (cannot remove the sole credential).
    """

    credential_id: str
    provider: str
    provider_display_name: str
    provider_user_id: str
    is_removable: bool


class Credential:
    """A user's authentication credential for a specific provider.

    Local credentials (email+password) require a hashed_secret.
    OAuth credentials (google, github, etc.) may have hashed_secret=None.
    """

    def __init__(
        self,
        credential_id: str,
        user_id: str,
        provider: str,
        provider_user_id: str,
        hashed_secret: str | None,
    ) -> None:
        if not provider.strip():
            raise ValueError("Provider cannot be empty")
        if not provider_user_id.strip():
            raise ValueError("Provider user ID cannot be empty")
        if provider == "local" and not hashed_secret:
            raise ValueError("Local credentials require a hashed secret")

        self.credential_id = credential_id
        self.user_id = user_id
        self.provider = provider
        self.provider_user_id = provider_user_id
        self.hashed_secret = hashed_secret
        self.created_at: datetime = datetime.now(timezone.utc)


class User:
    """User aggregate root for the Auth bounded context.

    Owns a collection of Credentials (one per auth provider).
    Email is the primary contact identifier, normalized to lowercase.
    """

    def __init__(
        self,
        user_id: str,
        email: str,
        display_name: str,
    ) -> None:
        email = email.strip().lower()
        if not email:
            raise ValueError("Email cannot be empty")
        if "@" not in email:
            raise ValueError("Invalid email format")

        display_name = display_name.strip()
        if not display_name:
            raise ValueError("Display name cannot be empty")
        if len(display_name) > 100:
            raise ValueError("Display name cannot exceed 100 characters")

        self.user_id = user_id
        self.email = email
        self.display_name = display_name
        self.is_active: bool = True
        self.created_at: datetime = datetime.now(timezone.utc)
        self.credentials: list[Credential] = []
        self.inviter_id: str | None = None  # set at registration if invited

    def add_credential(self, credential: Credential) -> None:
        """Add a credential. Only one credential per provider is allowed."""
        if self.has_credential_for_provider(credential.provider):
            raise ValueError(
                f"User already has a credential for provider '{credential.provider}'"
            )
        self.credentials.append(credential)

    def find_credential_by_provider(self, provider: str) -> Credential | None:
        """Return the credential for a given provider, or None."""
        for cred in self.credentials:
            if cred.provider == provider:
                return cred
        return None

    def has_credential_for_provider(self, provider: str) -> bool:
        """Check if the user has a credential for the given provider."""
        return self.find_credential_by_provider(provider) is not None

    def deactivate(self) -> None:
        """Deactivate the user. Raises if already inactive."""
        if not self.is_active:
            raise ValueError("User is already inactive")
        self.is_active = False

    def reactivate(self) -> None:
        """Reactivate the user. Raises if already active."""
        if self.is_active:
            raise ValueError("User is already active")
        self.is_active = True

    # -- Credential summary & inspection --------------------------------

    def list_credential_summaries(self) -> list[CredentialSummary]:
        """Return a read-only summary of every credential for UI display."""
        return [
            CredentialSummary(
                credential_id=cred.credential_id,
                provider=cred.provider,
                provider_display_name=_PROVIDER_DISPLAY_NAMES.get(
                    cred.provider, cred.provider.title()
                ),
                # For local credentials, display the user's email (human-readable).
                # provider_user_id stores user_id (UUID) to avoid denormalisation.
                provider_user_id=self.email
                if cred.provider == "local"
                else cred.provider_user_id,
                is_removable=self.can_remove_credential(cred.provider),
            )
            for cred in self.credentials
        ]

    def update_profile(
        self,
        *,
        email: str | None = None,
        display_name: str | None = None,
    ) -> None:
        """Update mutable profile fields.

        Caller is responsible for ensuring email uniqueness across all users
        before invoking this method.

        # TODO: trigger email-verification flow when email is changed.
        """
        if email is not None:
            email = email.strip().lower()
            if not email:
                raise ValueError("Email cannot be empty")
            if "@" not in email:
                raise ValueError("Invalid email format")
            self.email = email

        if display_name is not None:
            display_name = display_name.strip()
            if not display_name:
                raise ValueError("Display name cannot be empty")
            if len(display_name) > 100:
                raise ValueError("Display name cannot exceed 100 characters")
            self.display_name = display_name

    def can_remove_credential(self, provider: str) -> bool:
        """Check whether the credential for *provider* can be safely removed.

        Rules (Simple):
        - The provider must exist in the user's credentials.
        - The user must have at least two credentials (cannot remove the last one).
        """
        if not self.has_credential_for_provider(provider):
            return False
        return len(self.credentials) > 1
