"""Auth routes."""
from fastapi import APIRouter, Depends

from auth.models import UserPrincipal
from auth.dependencies import get_current_user

router = APIRouter(tags=["Auth"])


@router.get("/me", response_model=UserPrincipal)
async def me(user: UserPrincipal = Depends(get_current_user)) -> UserPrincipal:
    """Return the currently authenticated user."""
    return user
