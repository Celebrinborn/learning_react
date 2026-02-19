"""Auth domain models."""
from pydantic import BaseModel

# Abbrev	Full Name	Meaning
# iss	Issuer	Who issued the token
# sub	Subject	Who the token refers to (user ID)
# aud	Audience	Who the token is intended for
# exp	Expiration Time	When the token expires
# nbf	Not Before	Token is invalid before this time
# iat	Issued At	When the token was created


class Principal(BaseModel):
    """Authenticated user identity extracted from a validated token."""
    subject: str
    entra_object_id: str
    issuer: str
    audience: str
    expiration: int
    issued_at: int
    not_before: int
