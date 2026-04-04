"""AuthProvider protocol and AuthResult — strategy pattern for authentication."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from auth.domain.user import User


@dataclass(frozen=True)
class AuthResult:
    """Result of a successful authentication attempt."""

    user: User
    provider: str


class AuthProvider(Protocol):
    """Strategy for authenticating a user via a specific provider.

    Implementations: LocalAuthProvider (email+password), future OAuth providers.
    Adding a new provider = new class implementing this protocol + register in dict.
    No changes to existing code (OCP).
    """

    @property
    def provider_name(self) -> str: ...

    def authenticate(self, credential_data: dict[str, str]) -> AuthResult: ...
