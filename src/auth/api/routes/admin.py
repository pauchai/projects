"""Admin routes: invite code management (deprecated — invite codes moved to community).

This file remains as a stub to avoid import errors. Admin endpoints for invite
code management were removed when invite codes moved from auth to the community
bounded context.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/admin", tags=["admin"])
