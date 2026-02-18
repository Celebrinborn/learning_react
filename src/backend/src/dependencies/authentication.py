# src/backend/src/dependencies/authentication.py

from __future__ import annotations

from typing import Awaitable, Callable

from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from interfaces.auth import (
    AuthenticationError,
    iAuthentication,
)
from models.auth.user_principal import Principal

# Parses: Authorization: Bearer <token>
_bearer_scheme = HTTPBearer(auto_error=False)

# Public type alias for the dependency callable this module builds.
AuthenticationDependency = Callable[..., Awaitable[Principal]]


def build_authentication_dependency(authenticator: iAuthentication) -> AuthenticationDependency:
    """
    Build a FastAPI dependency that:
      1) extracts Bearer JWT from the Authorization header
      2) calls your framework-agnostic Authenticator
      3) translates domain errors into HTTP 401s

    This is intended to be called from your builder at startup so the returned
    dependency is already wired to the correct Authenticator instance.
    """

    async def get_current_principal(
        creds: HTTPAuthorizationCredentials | None = Security(_bearer_scheme),
    ) -> Principal:
        if creds is None or creds.scheme.lower() != "bearer" or not creds.credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing bearer token",
            )

        raw_jwt: str = creds.credentials
        try:
            return await authenticator.authenticate(raw_jwt)
        except AuthenticationError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )

    return get_current_principal
