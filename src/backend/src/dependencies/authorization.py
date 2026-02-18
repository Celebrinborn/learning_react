# src/backend/src/dependencies/authorization.py

from __future__ import annotations

import logging
from typing import Awaitable, Callable

from fastapi import HTTPException, Security, status

from interfaces.auth import (
    AuthorizationError,
    iAuthorization,
)
from models import UserRole
from models.auth.user_principal import Principal

logger = logging.getLogger()

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

# A dependency that returns the list of roles for the authenticated principal.
GetRolesDependency = Callable[..., Awaitable[list[UserRole]]]


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
        principal: Principal = Security(require_cnf_roles([[UserRole("admin")]]))
    """

    def require_cnf_roles(
        required_roles: list[list[UserRole]],
    ) -> AuthorizationDependency:
        # This is intentionally a thin adapter that composes AuthN -> AuthZ.
        async def _checker(
            principal: Principal = Security(authenticate),
        ) -> Principal:
            try:
                # If your authorizer enriches principal with roles, return that.
                result = await authorizer.required_cnf_roles(principal, required_roles)
                logger.debug(f"Successfully authenticated {principal.subject}")
                return result
            except AuthorizationError:
                logger.warning(
                    f"Authorization denied: {principal.subject} missing required "
                    f"roles {required_roles}", stack_info=True
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Forbidden",
                )

        return _checker

    return require_cnf_roles


def build_get_roles_dependency(
    *,
    authorizer: iAuthorization,
    authenticate: AuthenticationDependency,
) -> GetRolesDependency:
    """
    Build a FastAPI dependency that returns the authenticated principal's roles.
    """

    async def get_roles(
        principal: Principal = Security(authenticate),
    ) -> list[UserRole]:
        return await authorizer.get_roles(principal)

    return get_roles
