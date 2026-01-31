import json
from pathlib import Path
from typing import List, Optional
from datetime import datetime
import uuid

from dnd_backend.models.map import MapLocation, MapLocationCreate, MapLocationUpdate

# Get the data directory path (relative to project root)
DATA_DIR = Path(__file__).parent.parent.parent.parent / "data" / "maps"
DATA_DIR.mkdir(parents=True, exist_ok=True)

def _get_map_location_file_path(location_id: str) -> Path:
    """Get the file path for a map location"""
    return DATA_DIR / f"{location_id}.json"

def _load_all_map_locations() -> List[MapLocation]:
    """Load all map locations from disk"""
    locations = []
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

def create_map_location(location_data: MapLocationCreate) -> MapLocation:
    """Create a new map location and save to disk"""
    location_id = str(uuid.uuid4())
    now = datetime.utcnow()
    
    location = MapLocation(
        id=location_id,
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
    file_path = _get_map_location_file_path(location_id)
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

def update_map_location(location_id: str, location_data: MapLocationUpdate) -> Optional[MapLocation]:
    """Update a map location"""
    existing_location = get_map_location(location_id)
    
    if not existing_location:
        return None
    
    # Update fields
    update_dict = location_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(existing_location, field, value)
    
    existing_location.updated_at = datetime.utcnow()
    
    # Save to disk
    file_path = _get_map_location_file_path(location_id)
    with open(file_path, 'w') as f:
        json.dump(existing_location.model_dump(mode='json'), f, indent=2, default=str)
    
    return existing_location

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
