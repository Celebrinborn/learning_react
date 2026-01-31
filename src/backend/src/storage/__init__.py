"""Storage package"""
from .map import (
    create_map_location,
    get_map_location,
    get_all_map_locations,
    update_map_location,
    delete_map_location,
)
from .character import (
    create_character,
    get_character,
    get_all_characters,
    update_character,
    delete_character,
)

__all__ = [
    "create_map_location",
    "get_map_location",
    "get_all_map_locations",
    "update_map_location",
    "delete_map_location",
    "create_character",
    "get_character",
    "get_all_characters",
    "update_character",
    "delete_character",
]
