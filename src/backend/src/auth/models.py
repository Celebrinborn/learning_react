"""Auth domain models."""
from pydantic import BaseModel


class UserPrincipal(BaseModel):
    """Authenticated user identity extracted from a validated token."""
    subject: str
