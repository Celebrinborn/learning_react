"""Entra External ID authentication provider.

Validates JWT access tokens issued by Microsoft Entra External ID (CIAM).
Uses PyJWT for token decoding and signature verification.
"""
import logging
from typing import Any

import jwt
from jwt import PyJWKClient

from interfaces.auth.auth import AuthenticationError, iAuthentication
from models.auth.user_principal import Principal

logger = logging.getLogger(__name__)

class EntraAuthProvider(iAuthentication):
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

    def _decode_token(self, token: str) -> Principal:
        """Decode a JWT and return a Principal from its claims.

        Verifies the signature, audience, issuer, and temporal claims
        via PyJWT, then constructs a Principal from the payload.
        """
        key = self._get_signing_key(token)
        payload = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            audience=self._audience,
            issuer=self._issuer,
        )
        principal = Principal(
            subject=payload["sub"],
            entra_object_id=payload["oid"],
            issuer=payload["iss"],
            audience=payload["aud"],
            expiration=payload["exp"],
            issued_at=payload["iat"],
            not_before=payload["nbf"],
            name=payload.get("name"),
            prefered_username=payload.get("preferred_username")
        )
        return principal

    def _validate_claims(self, principal: Principal) -> None:
        """Validate that required claims contain meaningful values."""
        if not principal.subject:
            raise AuthenticationError("Invalid token: 'sub' claim must not be empty")
        if not principal.issuer:
            raise AuthenticationError("Invalid token: 'iss' claim must not be empty")
        if not principal.audience:
            raise AuthenticationError("Invalid token: 'aud' claim must not be empty")

    async def authenticate(self, token: str) -> Principal:
        try:
            principal = self._decode_token(token)
            self._validate_claims(principal)
            return principal
        except jwt.exceptions.ExpiredSignatureError:
            logger.warning("Token has expired")
            raise AuthenticationError("Token has expired")
        except jwt.exceptions.InvalidAudienceError:
            logger.warning(f"Token audience does not match expected audience '{self._audience}'")
            raise AuthenticationError("Invalid token audience")
        except jwt.exceptions.InvalidIssuerError:
            logger.warning(f"Token issuer does not match expected issuer '{self._issuer}'")
            raise AuthenticationError("Invalid token issuer")
        except jwt.exceptions.InvalidSignatureError:
            logger.warning("Token signature verification failed")
            raise AuthenticationError("Invalid token signature")
        except jwt.exceptions.ImmatureSignatureError:
            logger.warning("Token is not yet valid (nbf claim is in the future)")
            raise AuthenticationError("Token not yet valid")
        except jwt.exceptions.InvalidAlgorithmError:
            logger.warning("Token uses an unsupported algorithm")
            raise AuthenticationError("Invalid token algorithm")
        except jwt.exceptions.DecodeError:
            logger.warning("Token could not be decoded (malformed JWT)")
            raise AuthenticationError("Malformed token")
        except jwt.exceptions.MissingRequiredClaimError as e:
            logger.warning(f"Token is missing required claim: {e}")
            raise AuthenticationError("Token missing required claim")
        except jwt.exceptions.InvalidKeyError:
            logger.warning("Signing key is invalid for token verification")
            raise AuthenticationError("Invalid signing key")
        except jwt.exceptions.PyJWKClientError:
            logger.warning("Failed to fetch signing keys from JWKS endpoint")
            raise AuthenticationError("Could not retrieve signing keys")
        except jwt.PyJWTError:
            logger.warning("Token validation failed with unexpected error", exc_info=True)
            raise AuthenticationError("Invalid token")