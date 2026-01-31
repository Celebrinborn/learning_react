import json
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timezone
import re

from models.map import MapLocation

# Get the data directory path (relative to project root)
DATA_DIR = Path(__file__).parent.parent.parent.parent / "data" / "maps"
DATA_DIR.mkdir(parents=True, exist_ok=True)

def _sanitize_name(name: str) -> str:
    """Sanitize a name to be safe for use as a filename"""
    # Replace spaces and special chars with underscores, keep alphanumeric
    sanitized = re.sub(r'[^\w\s-]', '', name)
    sanitized = re.sub(r'[-\s]+', '_', sanitized)
    return sanitized.strip('_').lower()

def _get_map_location_file_path(location_name: str) -> Path:
    """Get the file path for a map location based on its name"""
    sanitized = _sanitize_name(location_name)
    return DATA_DIR / f"{sanitized}.json"

def _name_exists(name: str, exclude_name: Optional[str] = None) -> bool:
    """Check if a location with this name already exists"""
    file_path = _get_map_location_file_path(name)
    
    # If we're updating and the name hasn't changed, it's okay
    if exclude_name and _sanitize_name(name) == _sanitize_name(exclude_name):
        return False
    
    return file_path.exists()

def _load_all_map_locations() -> List[MapLocation]:
    """Load all map locations from disk"""
    locations: List[MapLocation] = []
    if not DATA_DIR.exists():
        return locations
    
    for file_path in DATA_DIR.glob("*.json"):
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                locations.append(MapLocation(**data))
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
    
    return locations

def create_map_location(location_data: MapLocation) -> MapLocation:
    """Create a new map location and save to disk"""
    # Check if name already exists
    if _name_exists(location_data.name):
        raise ValueError(f"A location with the name '{location_data.name}' already exists")
    
    now = datetime.now(timezone.utc)
    sanitized_id = _sanitize_name(location_data.name)
    
    # Create location with generated id and timestamps
    location = MapLocation(
        id=sanitized_id,
        name=location_data.name,
        description=location_data.description,
        latitude=location_data.latitude,
        longitude=location_data.longitude,
        map_id=location_data.map_id,
        icon_type=location_data.icon_type,
        created_at=now,
        updated_at=now
    )
    
    # Save to disk
    file_path = _get_map_location_file_path(location_data.name)
    with open(file_path, 'w') as f:
        json.dump(location.model_dump(mode='json'), f, indent=2, default=str)
    
    return location

def get_map_location(location_id: str) -> Optional[MapLocation]:
    """Get a map location by ID"""
    file_path = _get_map_location_file_path(location_id)
    
    if not file_path.exists():
        return None
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            return MapLocation(**data)
    except Exception as e:
        print(f"Error loading location {location_id}: {e}")
        return None

def get_all_map_locations(map_id: Optional[str] = None) -> List[MapLocation]:
    """Get all map locations, optionally filtered by map_id"""
    locations = _load_all_map_locations()
    
    if map_id:
        locations = [loc for loc in locations if loc.map_id == map_id]
    
    return locations

def update_map_location(location_id: str, location_data: MapLocation) -> Optional[MapLocation]:
    """Update a map location"""
    existing_location = get_map_location(location_id)
    
    if not existing_location:
        return None
    
    # Check if name is being changed and if new name already exists
    if location_data.name != existing_location.name:
        if _name_exists(location_data.name, exclude_name=existing_location.name):
            raise ValueError(f"A location with the name '{location_data.name}' already exists")
    
    # Get old file path before updating
    old_file_path = _get_map_location_file_path(existing_location.name)
    
    # Update all fields from location_data
    updated_location = MapLocation(
        id=_sanitize_name(location_data.name),
        name=location_data.name,
        description=location_data.description,
        latitude=location_data.latitude,
        longitude=location_data.longitude,
        map_id=location_data.map_id,
        icon_type=location_data.icon_type,
        created_at=existing_location.created_at,  # Keep original creation time
        updated_at=datetime.now(timezone.utc)
    )
    
    # Get new file path
    new_file_path = _get_map_location_file_path(updated_location.name)
    
    # If name changed, delete old file
    if old_file_path != new_file_path and old_file_path.exists():
        old_file_path.unlink()
    
    # Save to disk (new path if name changed)
    with open(new_file_path, 'w') as f:
        json.dump(updated_location.model_dump(mode='json'), f, indent=2, default=str)
    
    return updated_location

def delete_map_location(location_id: str) -> bool:
    """Delete a map location"""
    file_path = _get_map_location_file_path(location_id)
    
    if not file_path.exists():
        return False
    
    try:
        file_path.unlink()
        return True
    except Exception as e:
        print(f"Error deleting location {location_id}: {e}")
        return False
