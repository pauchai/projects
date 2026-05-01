"""ActivateUserWithInvite use case — activates a pending user via an invite code.

A user created through OAuth is initially in ``pending`` status and has limited
access. This use case:
1. Loads the user by user_id (extracted from the JWT by the caller).
2. Validates the invite code.
3. Calls ``user.activate()`` to promote status to ``active``.
4. Records the inviter relationship from the code.
5. Redeems the code and persists atomically.
6. Returns a new access token with status ``active``.
"""

from auth.domain.ports import TokenService, UnitOfWork


class ActivateUserWithInviteUseCase:
    """Activate a pending user by redeeming a valid invite code.

    Raises:
        LookupError: if the user is not found.
        ValueError: if the user is already active, the code is invalid,
                    or the user account is deactivated (is_active=False).
    """

    def __init__(self, uow: UnitOfWork, token_service: TokenService) -> None:
        self._uow = uow
        self._token_service = token_service

    def execute(self, user_id: str, invite_code: str) -> str:
        """Activate the user and return a fresh JWT with status='active'.

        Args:
            user_id: The user to activate (from the pending JWT sub claim).
            invite_code: The invite code submitted by the user.

        Returns:
            A new JWT access token with ``status='active'``.

        Raises:
            LookupError: if the user does not exist.
            ValueError: if the account is inactive (banned), already active,
                        or the invite code is invalid/exhausted/expired.
        """
        with self._uow as uow:
            user = uow.users.find_by_id(user_id)
            if user is None:
                raise LookupError(f"User {user_id!r} not found")

            if not user.is_active:
                raise ValueError("User account is inactive")

            # Validate invite code first (cheap guard before mutating user)
            normalized_code = invite_code.strip().upper()
            code_entity = uow.invite_codes.find_by_code(normalized_code)
            if code_entity is None or not code_entity.is_valid():
                raise ValueError("Invite code is invalid or has expired")

            # Promote pending → active
            user.activate()

            # Link inviter if not already set
            if user.inviter_id is None and code_entity.inviter_id is not None:
                user.inviter_id = code_entity.inviter_id

            # Redeem code
            code_entity.redeem()

            uow.users.save(user)
            uow.invite_codes.save(code_entity)
            uow.commit()

        return self._token_service.create_access_token(user.user_id, status=user.status)
