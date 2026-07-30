"""Auth domain models."""
from typing import Optional

from pydantic import BaseModel

# Abbrev	Full Name	Meaning
# iss	Issuer	Who issued the token
# sub	Subject	Who the token refers to (user ID)
# aud	Audience	Who the token is intended for
# exp	Expiration Time	When the token expires
# nbf	Not Before	Token is invalid before this time
# iat	Issued At	When the token was created


class Principal(BaseModel):
    """Authenticated user identity extracted from a validated token.

    Canonical identity is the (issuer, subject) pair, per standard OIDC practice --
    `subject` (sub) is only guaranteed unique within a given `issuer` (iss).
    """
    subject: str
    issuer: str
    audience: str
    expiration: int
    issued_at: int
    not_before: int
    # -- optional fields
    name: Optional[str]
    prefered_username: Optional[str]
    # Entra-specific (oid claim). Not present for non-Entra principals.
    # Kept optional for backward compat while users.json is manually
    # migrated to key by `subject`.
    entra_object_id: Optional[str] = None
