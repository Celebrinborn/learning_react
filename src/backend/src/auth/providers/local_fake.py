"""Local fake authentication provider for development.

Returns a hardcoded dev user without validating any token.
The frontend in local_fake mode sends no Authorization header.
"""
from typing import Callable, Any

from fastapi import Request

from auth.models import UserPrincipal


class LocalFakeAuthProvider:
    """Returns a hardcoded dev user. No token validation."""

    def dependency(self) -> Callable[..., Any]:
        """Return a FastAPI dependency that returns a fake user."""

        async def _get_current_user(request: Request) -> UserPrincipal:
            return UserPrincipal(subject="local-dev-user")

        return _get_current_user
