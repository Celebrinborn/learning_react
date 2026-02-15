"""Entra External ID authentication provider.

Validates JWT access tokens issued by Microsoft Entra External ID (CIAM).
Uses PyJWT for token decoding and signature verification.
"""
from typing import Any
import logging
import jwt
from jwt import PyJWKClient
from fastapi import Request, HTTPException

from src.models.auth.user_principal import Principal

logger = logging.getLogger(__name__)

class EntraAuthProvider:
    """Validates JWTs against Microsoft Entra External ID."""

    def __init__(self, issuer: str, audience: str, jwks_url: str) -> None:
        self._issuer = issuer
        self._audience = audience
        self._jwks_client = PyJWKClient(jwks_url)
        self._pem_key: bytes | None = None

    def _load_pem(self, pem: bytes) -> None:
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

    def _validate_decode_token(self, token: str) -> Principal:
        """Decode and validate a JWT, returning the authenticated user."""
        key = self._get_signing_key(token)
        payload = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            audience=self._audience,
            issuer=self._issuer,
        )
        # Validate required claims and their types
        if not isinstance(payload.get("sub"), str):
            raise HTTPException(status_code=401, detail="Invalid token: 'sub' claim must be a string")
        if not isinstance(payload.get("iss"), str):
            raise HTTPException(status_code=401, detail="Invalid token: 'iss' claim must be a string")
        if not isinstance(payload.get("aud"), str):
            raise HTTPException(status_code=401, detail="Invalid token: 'aud' claim must be a string")
        if not isinstance(payload.get("exp"), int):
            raise HTTPException(status_code=401, detail="Invalid token: 'exp' claim must be an integer")
        if not isinstance(payload.get("iat"), int):
            raise HTTPException(status_code=401, detail="Invalid token: 'iat' claim must be an integer")
        if not isinstance(payload.get("nbf"), int):
            raise HTTPException(status_code=401, detail="Invalid token: 'nbf' claim must be an integer")
        if not isinstance(payload.get("jti"), str):
            raise HTTPException(status_code=401, detail="Invalid token: 'jti' claim must be a string")

        return Principal(
            subject=payload["sub"],
            issuer=payload["iss"],
            audience=payload["aud"],
            expiration=payload["exp"],
            issued_at=payload["iat"],
            not_before=payload["nbf"],
            jwt_id=payload["jti"]
        )

    async def get_current_user(self, request: Request) -> Principal:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            logger.warning("Missing or invalid Authorization header", stack_info=True)
            raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

        token = auth_header[len("Bearer "):]
        try:
            return self._validate_decode_token(token)
        except jwt.PyJWTError:
            logger.warning("Invalid token", stack_info=True)
            raise HTTPException(status_code=401, detail="Invalid token")