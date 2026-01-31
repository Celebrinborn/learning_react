from fastapi import APIRouter, HTTPException
from typing import Optional, List

from dnd_backend.models.map import MapLocation, MapLocationCreate, MapLocationUpdate
from dnd_backend.storage.map import (
    create_map_location,
    get_map_location,
    get_all_map_locations,
    update_map_location,
    delete_map_location,
)

router = APIRouter(prefix="/api/map-locations", tags=["Map Locations"])

@router.post("", response_model=MapLocation, status_code=201)
async def create_location(location: MapLocationCreate):
    """Create a new map location"""
    try:
        return create_map_location(location)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("", response_model=List[MapLocation])
async def list_locations(map_id: Optional[str] = None):
    """Get all map locations, optionally filtered by map_id"""
    return get_all_map_locations(map_id=map_id)

@router.get("/{location_id}", response_model=MapLocation)
async def get_location(location_id: str):
    """Get a specific map location by ID"""
    location = get_map_location(location_id)
    if not location:
        raise HTTPException(status_code=404, detail="Map location not found")
    return location

@router.put("/{location_id}", response_model=MapLocation)
async def update_location(location_id: str, location_data: MapLocationUpdate):
    """Update a map location"""
    try:
        location = update_map_location(location_id, location_data)
        if not location:
            raise HTTPException(status_code=404, detail="Map location not found")
        return location
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{location_id}")
async def delete_location(location_id: str):
    """Delete a map location"""
    success = delete_map_location(location_id)
    if not success:
        raise HTTPException(status_code=404, detail="Map location not found")
    return {"message": "Map location deleted successfully"}
