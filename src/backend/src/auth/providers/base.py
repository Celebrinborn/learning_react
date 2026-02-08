"""Auth provider interface."""
from typing import Protocol, Callable, Any

from auth.models import UserPrincipal


class IAuthProvider(Protocol):
    """Interface for authentication providers."""

    def dependency(self) -> Callable[..., Any]:
        """Return a FastAPI dependency that authenticates requests.

        The returned callable should:
        - Extract the Bearer token from the Authorization header
        - Validate the token
        - Return a UserPrincipal on success
        - Raise HTTPException(401) on failure
        """
        ...
