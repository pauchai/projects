"""PKCE (Proof Key for Code Exchange) service for OAuth 2.0 security.

Generates cryptographically secure ``code_verifier`` / ``code_challenge``
pairs and random ``state`` parameters as specified in RFC 7636.

This is an infrastructure utility — it has no domain dependencies.
"""

from __future__ import annotations

import base64
import hashlib
import secrets


class PKCEService:
    """Generate PKCE parameters for OAuth 2.0 authorization flows.

    Usage::

        pkce = PKCEService()
        state = pkce.generate_state()
        verifier, challenge = pkce.generate_pkce_pair()
        # Pass challenge + state to authorization URL
        # Store verifier + state for callback validation
    """

    def generate_state(self) -> str:
        """Generate a cryptographically random URL-safe state parameter."""
        return secrets.token_urlsafe(32)

    def generate_pkce_pair(self) -> tuple[str, str]:
        """Generate a ``(code_verifier, code_challenge)`` pair.

        The verifier is 43-128 characters of URL-safe random bytes.
        The challenge is ``BASE64URL(SHA256(code_verifier))`` per RFC 7636.
        """
        verifier = secrets.token_urlsafe(32)
        digest = hashlib.sha256(verifier.encode("ascii")).digest()
        challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
        return verifier, challenge
