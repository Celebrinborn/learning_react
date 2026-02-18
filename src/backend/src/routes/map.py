import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Security

from builder import AppBuilder
from dependencies import authenticate, require_cnf_roles
from models.auth.roles import UserRole
from models.auth.user_principal import Principal
from models.map import MapLocation, MapLocationCreate, MapLocationUpdate
from storage.map import MapStorage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/map-locations", tags=["Map Locations"])

_builder = AppBuilder()
_map_storage = MapStorage(_builder.build_map_blob_storage())


@router.post("", response_model=MapLocation, status_code=201)
async def create_location(
    location: MapLocationCreate,
    principal: Principal = Security(authenticate),
    _: Principal = Security(require_cnf_roles([[UserRole.DM]])),
):
    """Create a new map location"""
    logger.info(f"Creating map location: {location.name} by {principal.subject}")
    try:
        return await _map_storage.create_map_location(location)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=List[MapLocation])
async def list_locations(
    map_id: Optional[str] = None,
    principal: Principal = Security(authenticate),
    _: Principal = Security(require_cnf_roles([[UserRole.DM]])),
):
    """Get all map locations, optionally filtered by map_id"""
    logger.info(
        f"Listing map locations with filter: map_id={map_id} by {principal.subject}"
    )
    locations: list[MapLocation] = await _map_storage.get_all_map_locations(
        map_id=map_id
    )
    logger.info(
        f"Retrieved {len(locations)} map locationswith filter: map_id={map_id}"
    )
    return locations


@router.get("/{location_id}", response_model=MapLocation)
async def get_location(
    location_id: str,
    principal: Principal = Security(authenticate),
    _: Principal = Security(require_cnf_roles([[UserRole.DM]])),
):
    """Get a specific map location by ID"""
    logger.info(f"Getting map location with ID: {location_id} by {principal.subject}")
    location = await _map_storage.get_map_location(location_id)
    if not location:
        logger.warning(f"Map location with ID {location_id} not found")
        raise HTTPException(status_code=404, detail="Map location not found")
    logger.info(f"Map location with ID {location_id} retrieved successfully")
    return location


@router.put("/{location_id}", response_model=MapLocation)
async def update_location(
    location_id: str,
    location_data: MapLocationUpdate,
    principal: Principal = Security(authenticate),
    _: Principal = Security(require_cnf_roles([[UserRole.DM]])),
):
    """Update a map location"""
    logger.info(f"Updating map location with ID: {location_id} by {principal.subject}")
    try:
        location = await _map_storage.update_map_location(location_id, location_data)
        if not location:
            logger.warning(
                f"Map location with ID {location_id} not found for update"
            )
            raise HTTPException(status_code=404, detail="Map location not found")
        return location
    except ValueError as e:
        logger.error(f"Error updating map location with ID {location_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{location_id}")
async def delete_location(
    location_id: str,
    principal: Principal = Security(authenticate),
    _: Principal = Security(require_cnf_roles([[UserRole.DM]])),
):
    """Delete a map location"""
    logger.info(f"Deleting map location with ID: {location_id} by {principal.subject}")
    success = await _map_storage.delete_map_location(location_id)
    if not success:
        logger.warning(f"Map location with ID {location_id} not found for deletion")
        raise HTTPException(status_code=404, detail="Map location not found")
    logger.info(f"Map location with ID {location_id} deleted successfully")
    return {"message": "Map location deleted successfully"}
