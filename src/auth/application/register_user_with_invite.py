"""RegisterUserWithInvite use case — replaces open registration.

Extends RegisterUserUseCase with invite code validation:
1. Validate invite code is active and not exhausted/expired.
2. Create user, link inviter_id from the code's inviter.
3. Redeem the code (decrement uses_left).
4. Persist atomically.

Returns an ``InviteCodeResult`` so the calling handler can route by scope
(e.g. call ``RedeemProjectInviteUseCase`` when scope="project") without
the use case knowing about the project_collaboration context (SRP).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from auth.domain.ports import PasswordHasher, UnitOfWork
from auth.domain.user import Credential, User


@dataclass(frozen=True)
class InviteCodeResult:
    """Carries registration outcome and scope metadata back to the handler."""

    user_id: str
    scope: str
    project_id: str | None
    community_id: str | None
    role: str | None


class RegisterUserWithInviteUseCase:
    """Register a new user using a valid invite code.

    Raises:
        ValueError: if the invite code is invalid/exhausted/expired,
                    or the email is already registered.
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
        invite_code: str,
    ) -> InviteCodeResult:
        """Register a new user. Returns an InviteCodeResult.

        Args:
            user_id: Pre-generated UUID for the new user.
            email: User email address.
            password: Plain-text password (will be hashed).
            display_name: Display name.
            invite_code: The invite code submitted by the user.

        Raises:
            ValueError: on invalid code or duplicate email.
        """
        with self._uow as uow:
            # 1. Validate invite code
            normalized_code = invite_code.strip().upper()
            code_entity = uow.invite_codes.find_by_code(normalized_code)
            if code_entity is None or not code_entity.is_valid():
                raise ValueError("Invite code is invalid or has expired")

            # 2. Check email uniqueness
            if uow.users.find_by_email(email) is not None:
                raise ValueError("Email already registered")

            # 3. Create user
            user = User(user_id=user_id, email=email, display_name=display_name)
            user.inviter_id = code_entity.inviter_id  # may be None for admin codes

            # 4. Hash password and attach local credential
            hashed = self._password_hasher.hash(password)
            credential = Credential(
                credential_id=str(uuid.uuid4()),
                user_id=user_id,
                provider="local",
                provider_user_id=user_id,
                hashed_secret=hashed,
            )
            user.add_credential(credential)

            # 5. Redeem invite code
            code_entity.redeem()

            # 6. Persist
            uow.users.save(user)
            uow.invite_codes.save(code_entity)
            uow.commit()

        return InviteCodeResult(
            user_id=user.user_id,
            scope=code_entity.scope,
            project_id=code_entity.project_id,
            community_id=code_entity.community_id,
            role=code_entity.role,
        )

