"""Entra External ID authentication provider.

Validates JWT access tokens issued by Microsoft Entra External ID (CIAM).
Uses PyJWT for token decoding and signature verification.
"""
from typing import Callable, Any

import jwt
from jwt import PyJWKClient
from fastapi import Request, HTTPException

from auth.models import UserPrincipal


class EntraAuthProvider:
    """Validates JWTs against Microsoft Entra External ID."""

    def __init__(self, issuer: str, audience: str, jwks_url: str) -> None:
        self._issuer = issuer
        self._audience = audience
        self._jwks_client = PyJWKClient(jwks_url)
        self._pem_key: bytes | None = None

    def load_pem(self, pem: bytes) -> None:
        """Load a PEM-encoded public key directly, bypassing JWKS fetch.

        Used in tests to avoid network calls.
        """
        self._pem_key = pem

    def _get_signing_key(self, token: str) -> Any:
        """Get the key to verify the token signature."""
        if self._pem_key is not None:
            return self._pem_key
        signing_key = self._jwks_client.get_signing_key_from_jwt(token)
        return signing_key.key

    def _validate_token(self, token: str) -> UserPrincipal:
        """Decode and validate a JWT, returning the authenticated user."""
        key = self._get_signing_key(token)
        payload = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            audience=self._audience,
            issuer=self._issuer,
        )
        return UserPrincipal(subject=payload["sub"])

    def dependency(self) -> Callable[..., Any]:
        """Return a FastAPI dependency that authenticates requests."""
        provider = self

        async def _get_current_user(request: Request) -> UserPrincipal:
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

            token = auth_header[len("Bearer "):]
            try:
                return provider._validate_token(token)
            except jwt.PyJWTError:
                raise HTTPException(status_code=401, detail="Invalid token")

        return _get_current_user
