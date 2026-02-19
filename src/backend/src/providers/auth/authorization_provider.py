import logging

from interfaces.auth import iAuthorization
from interfaces.auth.auth import AuthorizationError
from models import UserRole
from models.auth.user_principal import Principal

logger = logging.getLogger(__name__)


class HardcodedAuthorizationProvider(iAuthorization):
    """
    A simple local authentication provider for testing and development.
    Uses a hardcoded list of subs.
    This is not authentication, only authorization based on a verified sub claim.
    """

    def __init__(self):
        self.valid_oids: dict[str, list[UserRole]] = {
            "25edd424-4428-4952-80e1-9e0a3fe718a6":
                [
                    # UserRole.ADMIN, 
                    UserRole.DM, 
                    UserRole.PLAYER
                ], # My personal test account, has all roles
        }

    async def _get_user_roles(self, user: Principal) -> list[UserRole]:
        """Get the roles for a given user."""
        logger.debug(f"Getting roles for user: {user.entra_object_id}")
        if user.entra_object_id in self.valid_oids:
            logger.info(f"User {user.entra_object_id} has roles: {self.valid_oids[user.entra_object_id]}")
            return self.valid_oids[user.entra_object_id]
        else:
            logger.warning(f"Unauthorized access attempt by sub: {user.entra_object_id}")
            return []
    async def required_cnf_roles(
        self,
        principal: Principal,
        required_roles: list[list[UserRole]],
    ) -> Principal:
        """
        Ensure the principal has all required roles.

        Args:
            principal: Authenticated identity.
            required_roles: CNF list of role sets. Access is granted if the principal has at least one role from each set.
                Example: [["admin"], ["editor", "writer"]] means the principal must have "admin
                AND at least one of "editor" or "writer".

        Returns:
            Principal (optionally enriched with roles).

        Raises:
            AuthorizationError: If access should be denied.
        """
        user_roles = await self._get_user_roles(principal)
        for role_set in required_roles:
            if not any(role in user_roles for role in role_set):
                logger.warning(f"User {principal.subject} lacks required roles: {role_set}")
                raise AuthorizationError(f"User {principal.subject} lacks required roles: {role_set}")
        return principal

    async def get_roles(self, principal: Principal) -> list[UserRole]:
        """Return the roles assigned to the given principal."""
        return await self._get_user_roles(principal)