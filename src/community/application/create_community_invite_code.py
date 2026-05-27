from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from community.domain.community_role import CommunityRole
from community.domain.invite_code import CommunityInviteCode
from community.domain.ports import CommunityUnitOfWork


class CreateCommunityInviteCodeUseCase:
    def __init__(self, uow: CommunityUnitOfWork) -> None:
        self._uow = uow

    def execute(
        self,
        community_id: str,
        caller_id: str,
        *,
        max_uses: int = 1,
        expires_in_days: int = 7,
        role: str = "member",
    ) -> CommunityInviteCode:
        with self._uow as uow:
            community = uow.communities.find_by_id(community_id)
            if community is None:
                raise LookupError(f"Community '{community_id}' not found")

            member = community._find_active_membership(caller_id)
            if member is None or member.role not in (
                CommunityRole.OWNER,
                CommunityRole.ADMIN,
            ):
                raise PermissionError(
                    "Only owner or admin can create invite codes"
                )

            code = CommunityInviteCode(
                code_id=str(uuid.uuid4()),
                code=self._generate_code(),
                community_id=community_id,
                issued_by=caller_id,
                max_uses=max_uses,
                expires_at=datetime.now(timezone.utc) + timedelta(days=expires_in_days),
                role=role,
            )
            uow.invite_codes.save(code)
            uow.commit()
            return code

    @staticmethod
    def _generate_code() -> str:
        import secrets
        import string

        chars = string.ascii_uppercase + string.digits
        return "".join(secrets.choice(chars) for _ in range(8))
