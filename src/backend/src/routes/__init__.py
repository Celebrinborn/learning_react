"""Routes package"""
from .map import router as map_router
from .character import router as character_router
from .homebrew import router as homebrew_router

__all__ = ["map_router", "character_router", "homebrew_router"]
