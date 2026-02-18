from abc import ABC, abstractmethod
from models.auth.user_principal import Principal
from models import UserRole

class AuthenticationError(Exception):
    """Raised when authentication fails (invalid token, expired, etc.)."""
    pass


class iAuthentication(ABC):
    """
    Contract for authenticating a request.

    This interface is intentionally framework-agnostic.
    It does not know about HTTP headers, FastAPI, or transport concerns.

    Implementations may validate:
      - JWT signatures (Entra, Auth0, etc.)
      - API keys
      - mTLS identities
      - Session cookies

    The only responsibility is:
        Given raw credentials → return a Principal or raise AuthenticationError.
    """

    @abstractmethod
    async def get_current_user(self, token: str) -> Principal:
        """
        Validate credentials and return an authenticated Principal.

        Args:
            token: Raw JWT string.

        Returns:
            Principal: Authenticated identity.

        Raises:
            AuthenticationError: If validation fails.
        """
        raise NotImplementedError

class AuthorizationError(Exception):
    """Raised when a principal lacks required permissions."""
    pass


class iAuthorization(ABC):
    """
    Contract for enforcing access control.

    This interface is framework-agnostic and transport-agnostic.

    Implementations may consult:
      - Database role tables
      - ACL tables
      - External policy engines
      - Attribute-based access control logic
      - Feature flags

    Responsibility:
        Given an authenticated Principal → decide if access is allowed.
    """

    @abstractmethod
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
        raise NotImplementedError