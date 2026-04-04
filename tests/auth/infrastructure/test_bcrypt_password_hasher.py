"""Tests for BcryptPasswordHasher — infrastructure adapter."""

from auth.infrastructure.bcrypt_password_hasher import BcryptPasswordHasher


class TestBcryptPasswordHasher:
    """BcryptPasswordHasher wraps passlib bcrypt for the PasswordHasher port."""

    def test_hash_returns_non_empty_string(self) -> None:
        hasher = BcryptPasswordHasher()
        hashed = hasher.hash("my_secret_password")
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_hash_is_not_plaintext(self) -> None:
        hasher = BcryptPasswordHasher()
        hashed = hasher.hash("my_secret_password")
        assert hashed != "my_secret_password"

    def test_verify_correct_password(self) -> None:
        hasher = BcryptPasswordHasher()
        hashed = hasher.hash("correct_password")
        assert hasher.verify("correct_password", hashed) is True

    def test_verify_wrong_password(self) -> None:
        hasher = BcryptPasswordHasher()
        hashed = hasher.hash("correct_password")
        assert hasher.verify("wrong_password", hashed) is False

    def test_different_hashes_for_same_password(self) -> None:
        hasher = BcryptPasswordHasher()
        h1 = hasher.hash("same_password")
        h2 = hasher.hash("same_password")
        # bcrypt produces different salts each time
        assert h1 != h2

    def test_verify_still_works_with_different_hashes(self) -> None:
        hasher = BcryptPasswordHasher()
        h1 = hasher.hash("same_password")
        h2 = hasher.hash("same_password")
        assert hasher.verify("same_password", h1) is True
        assert hasher.verify("same_password", h2) is True
