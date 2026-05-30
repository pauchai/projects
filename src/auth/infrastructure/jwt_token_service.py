"""JwtTokenService — infrastructure adapter for TokenService port.

Uses PyJWT to create and decode HS256 access tokens.
"""

from datetime import datetime, timedelta, timezone

import jwt


class JwtTokenService:
    """Implements TokenService Protocol using PyJWT."""

    def __init__(
        self,
        secret: str,
        algorithm: str = "HS256",
        expire_minutes: int = 60,
    ) -> None:
        self._secret = secret
        self._algorithm = algorithm
        self._expire_minutes = expire_minutes

    def create_access_token(self, user_id: str, status: str = "active") -> str:
        """Create a signed JWT with user_id in 'sub' and status in 'st' claim."""
        now = datetime.now(timezone.utc)
        payload = {
            "sub": user_id,
            "st": status,
            "iat": now,
            "exp": now + timedelta(minutes=self._expire_minutes),
        }
        return jwt.encode(payload, self._secret, algorithm=self._algorithm)

    def decode_token(self, token: str) -> str:
        """Decode a JWT and return the user_id. Raises ValueError if invalid."""
        try:
            payload = jwt.decode(token, self._secret, algorithms=[self._algorithm])
            user_id: str = payload["sub"]
            return user_id
        except (jwt.InvalidTokenError, KeyError) as exc:
            raise ValueError("Invalid token") from exc

    def decode_token_full(self, token: str) -> dict:
        """Decode a JWT and return the full payload dict (user_id, status).

        Returns a dict with keys: ``user_id`` (str) and ``status`` (str).
        Raises ValueError if the token is invalid or missing required claims.
        """
        try:
            payload = jwt.decode(token, self._secret, algorithms=[self._algorithm])
            return {
                "user_id": payload["sub"],
                "status": payload.get("st", "active"),
            }
        except (jwt.InvalidTokenError, KeyError) as exc:
            raise ValueError("Invalid token") from exc
