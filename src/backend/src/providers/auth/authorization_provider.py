from interfaces import IAuthorizationProvider
from models import UserRole
from src.models.auth.user_principal import Principal
import logging

logger = logging.getLogger(__name__)


class HardcodedAuthorizationProvider(IAuthorizationProvider):
    """
    A simple local authentication provider for testing and development.
    Uses a hardcoded list of subs.
    This is not authentication, only authorization based on a verified sub claim.
    """

    def __init__(self):
        self.valid_subs: dict[str, list[UserRole]] = {
            "JZOCNP0bu8U3ArC6m2SA5AEZZSKy4kFMQw7j1LZOcQE":
                [UserRole.ADMIN, UserRole.DM], # My personal test account, has all roles
        }

    async def get_user_roles(self, user: Principal) -> list[UserRole]:
        """Get the roles for a given user."""
        logger.debug(f"Getting roles for user: {user.subject}")
        if user.subject in self.valid_subs:
            logger.info(f"User {user.subject} has roles: {self.valid_subs[user.subject]}")
            return self.valid_subs[user.subject]
        else:
            logger.warning(f"Unauthorized access attempt by sub: {user.subject}")
            return []
