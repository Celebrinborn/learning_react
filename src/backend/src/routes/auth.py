"""Auth routes."""
from fastapi import APIRouter, Security

from dependencies import authenticate, require_cnf_roles
from models.auth.roles import UserRole
from models.auth.user_principal import Principal

router = APIRouter(tags=["Auth"])


@router.get("/me", response_model=Principal)
async def me(user: Principal = Security(authenticate)) -> Principal:
    """Return the currently authenticated user."""
    return user

@router.get("/me_is_admin")
async def me_is_admin(
    user: Principal = Security(authenticate),
    _: Principal = Security(require_cnf_roles([[UserRole.ADMIN]]))
) -> dict[str, bool]:
    """Check if the current user has admin role."""
    return {"is_admin": True}

@router.get("/me_is_dm")
async def me_is_dm(
    user: Principal = Security(authenticate),
    _: Principal = Security(require_cnf_roles([[UserRole.DM]]))
) -> dict[str, bool]:
    """Check if the current user has DM role."""
    return {"is_dm": True}

@router.get("/me_is_player")
async def me_is_player(
    user: Principal = Security(authenticate),
    _: Principal = Security(require_cnf_roles([[UserRole.PLAYER]]))
) -> dict[str, bool]:
    """Check if the current user has player role."""
    return {"is_player": True}

    
