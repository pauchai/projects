"""Unit tests for PKCE (Proof Key for Code Exchange) service — TDD."""

import base64
import hashlib

from auth.infrastructure.pkce_service import PKCEService


class TestPKCEService:
    """Tests for PKCE code_verifier / code_challenge generation."""

    def test_generate_state_returns_nonempty_string(self) -> None:
        service = PKCEService()

        state = service.generate_state()

        assert isinstance(state, str)
        assert len(state) > 0

    def test_generate_state_is_unique_each_call(self) -> None:
        service = PKCEService()

        state_a = service.generate_state()
        state_b = service.generate_state()

        assert state_a != state_b

    def test_generate_state_is_url_safe(self) -> None:
        service = PKCEService()

        state = service.generate_state()

        # URL-safe means no +, /, = characters
        assert "+" not in state
        assert "/" not in state

    def test_generate_pkce_pair_returns_verifier_and_challenge(self) -> None:
        service = PKCEService()

        verifier, challenge = service.generate_pkce_pair()

        assert isinstance(verifier, str)
        assert isinstance(challenge, str)
        assert len(verifier) > 0
        assert len(challenge) > 0

    def test_code_verifier_length_within_rfc_bounds(self) -> None:
        """RFC 7636: code_verifier must be 43-128 characters."""
        service = PKCEService()

        verifier, _ = service.generate_pkce_pair()

        assert 43 <= len(verifier) <= 128

    def test_code_challenge_is_sha256_of_verifier(self) -> None:
        """RFC 7636: code_challenge = BASE64URL(SHA256(code_verifier))."""
        service = PKCEService()

        verifier, challenge = service.generate_pkce_pair()

        # Manually compute expected challenge
        digest = hashlib.sha256(verifier.encode("ascii")).digest()
        expected = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")

        assert challenge == expected

    def test_generate_pkce_pair_is_unique_each_call(self) -> None:
        service = PKCEService()

        verifier_a, challenge_a = service.generate_pkce_pair()
        verifier_b, challenge_b = service.generate_pkce_pair()

        assert verifier_a != verifier_b
        assert challenge_a != challenge_b

    def test_code_verifier_is_url_safe(self) -> None:
        service = PKCEService()

        verifier, _ = service.generate_pkce_pair()

        # URL-safe base64 characters only
        assert "+" not in verifier
        assert "/" not in verifier
