"""Auth dependencies for FastAPI route injection."""
from fastapi import Request, HTTPException

from auth.models import UserPrincipal


async def get_current_user(request: Request) -> UserPrincipal:
    """Default auth dependency. Override via app.dependency_overrides in production."""
    raise HTTPException(status_code=401, detail="Auth provider not configured")
