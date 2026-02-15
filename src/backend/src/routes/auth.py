"""Auth routes."""
from fastapi import APIRouter, Depends

from src.models.auth.user_principal import Principal
from auth.dependencies import get_current_user

router = APIRouter(tags=["Auth"])


@router.get("/me", response_model=Principal)
async def me(user: Principal = Depends(get_current_user)) -> Principal:
    """Return the currently authenticated user."""
    return user
