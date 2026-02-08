"""Routes package"""
from .map import router as map_router
from .character import router as character_router
from .homebrew import router as homebrew_router
from .auth import router as auth_router

__all__ = ["map_router", "character_router", "homebrew_router", "auth_router"]
