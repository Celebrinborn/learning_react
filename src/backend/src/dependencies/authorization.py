# src/backend/src/dependencies/authorization.py

from __future__ import annotations

from typing import Awaitable, Callable

from fastapi import HTTPException, Security, status

from interfaces.auth import (
    AuthorizationError,
    iAuthorization,
)
from models.auth.user_principal import Principal
from models import UserRole

# ---------------------------------------------------------------------------
# FastAPI Dependency Type Definitions
# ---------------------------------------------------------------------------

# A dependency that returns an authenticated Principal.
#
# This is the callable you pass into:
#     Security(get_current_principal)
#
# It is responsible for authentication only.
# It does NOT enforce any role or permission checks.
AuthenticationDependency = Callable[..., Awaitable[Principal]]


# A dependency that enforces authorization policy and returns the Principal
# if access is allowed.
#
# This is what is returned from require_roles(...)
# and used like:
#     Security(require_roles(policy))
AuthorizationDependency = Callable[..., Awaitable[Principal]]


# A factory that builds authorization dependencies.
#
# You call it with a role policy, and it returns a FastAPI dependency
# that enforces that policy.
#
# Example:
#     require_roles = build_authorization_factory(...)
#     principal: Principal = Security(require_roles([[UserRole("admin")]]))
AuthorizationFactory = Callable[[list[list[UserRole]]], AuthorizationDependency]


def build_authorization_factory(
    *,
    authorizer: iAuthorization,
    authenticate: AuthenticationDependency,
) -> AuthorizationFactory:
    """
    Build a factory for authorization dependencies.

    - `authenticate` is the AuthN dependency returned by build_authentication_dependency(...)
    - `authorizer` is your framework-agnostic Authorizer that checks roles/permissions
      (typically via your internal DB keyed by principal.sub)

    Usage (in routes):
        principal: Principal = Security(require_roles([[UserRole("admin")]]))
    """

    def require_roles(required_roles: list[list[UserRole]]) -> AuthorizationDependency:
        # This is intentionally a thin adapter that composes AuthN -> AuthZ.
        async def _checker(
            principal: Principal = Security(authenticate),
        ) -> Principal:
            try:
                # If your authorizer enriches principal with roles, return that.
                return await authorizer.require_roles(principal, required_roles)
            except AuthorizationError:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Forbidden",
                )

        return _checker
    return require_roles