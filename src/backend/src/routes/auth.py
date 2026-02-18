"""Auth routes."""
from fastapi import APIRouter, Security

from dependencies import authenticate
from models.auth.user_principal import Principal

router = APIRouter(tags=["Auth"])


@router.get("/me", response_model=Principal)
async def me(user: Principal = Security(authenticate)) -> Principal:
    """Return the currently authenticated user."""
    return user
