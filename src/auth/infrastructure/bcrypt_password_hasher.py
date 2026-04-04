"""BcryptPasswordHasher — infrastructure adapter for PasswordHasher port.

Uses the bcrypt library directly to hash and verify passwords.
"""

import bcrypt


class BcryptPasswordHasher:
    """Implements PasswordHasher Protocol using bcrypt.

    Passwords are hashed with a random salt using bcrypt.
    bcrypt natively truncates passwords to 72 bytes.
    """

    def __init__(self, rounds: int = 12) -> None:
        self._rounds = rounds

    def hash(self, plain_password: str) -> str:
        """Hash a plain-text password using bcrypt."""
        password_bytes = plain_password.encode("utf-8")
        salt = bcrypt.gensalt(rounds=self._rounds)
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode("utf-8")

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a plain-text password against a bcrypt hash."""
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
