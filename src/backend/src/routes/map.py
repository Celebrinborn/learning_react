from fastapi import APIRouter, HTTPException
from fastapi.security import OAuth2PasswordBearer
from typing import Optional, List
import logging
from opentelemetry import trace

from models.map import MapLocation, MapLocationCreate, MapLocationUpdate
from storage.map import (
    create_map_location,
    get_map_location,
    get_all_map_locations,
    update_map_location,
    delete_map_location,
)
from telemetry import get_tracer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/map-locations", tags=["Map Locations"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@router.post("", response_model=MapLocation, status_code=201)
async def create_location(location: MapLocationCreate):
    """Create a new map location"""
    logger.info(f"Creating map location: {location.name}")
    tracer = get_tracer()
    with tracer.start_as_current_span("create_map_location_handler") as span:
        span.set_attribute("location.name", location.name)
        try:
            return create_map_location(location)
        except ValueError as e:
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
            raise HTTPException(status_code=400, detail=str(e))


@router.get("",response_model=List[MapLocation])
async def list_locations(map_id: Optional[str] = None):
    """Get all map locations, optionally filtered by map_id"""
    logger.info(f"Listing map locations with filter: map_id={map_id}")
    tracer = get_tracer()
    with tracer.start_as_current_span("list_map_locations_handler") as span:
        if map_id:
            span.set_attribute("filter.map_id", map_id)
            # with count of returned locations and size
        locations: list[MapLocation] = get_all_map_locations(map_id=map_id)
        logger.info(
            f"Retrieved {len(locations)} map locations" f"with filter: map_id={map_id}"
        )
        return locations


@router.get("/{location_id}", response_model=MapLocation)
async def get_location(location_id: str):
    """Get a specific map location by ID"""
    logger.info(f"Getting map location with ID: {location_id}")
    tracer = get_tracer()
    with tracer.start_as_current_span("get_map_location_handler") as span:
        span.set_attribute("location.id", location_id)
        location = get_map_location(location_id)
        if not location:
            span.set_status(
                trace.Status(trace.StatusCode.ERROR, "Map location not found")
            )
            logger.warning(f"Map location with ID {location_id} not found")
            raise HTTPException(status_code=404, detail="Map location not found")
        logger.info(f"Map location with ID {location_id} retrieved successfully")
        return location


@router.put("/{location_id}", response_model=MapLocation)
async def update_location(location_id: str, location_data: MapLocationUpdate):
    """Update a map location"""
    logger.info(f"Updating map location with ID: {location_id}")
    tracer = get_tracer()
    with tracer.start_as_current_span("update_map_location_handler") as span:
        span.set_attribute("location.id", location_id)
        try:
            location = update_map_location(location_id, location_data)
            if not location:
                span.set_status(
                    trace.Status(trace.StatusCode.ERROR, "Map location not found")
                )
                logger.warning(
                    f"Map location with ID {location_id} not found for update"
                )
                raise HTTPException(status_code=404, detail="Map location not found")
            return location
        except ValueError as e:
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
            logger.error(f"Error updating map location with ID {location_id}: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{location_id}")
async def delete_location(location_id: str):
    """Delete a map location"""
    logger.info(f"Deleting map location with ID: {location_id}")
    tracer = get_tracer()
    with tracer.start_as_current_span("delete_map_location_handler") as span:
        span.set_attribute("location.id", location_id)
        success = delete_map_location(location_id)
        if not success:
            span.set_status(
                trace.Status(trace.StatusCode.ERROR, "Map location not found")
            )
            logger.warning(f"Map location with ID {location_id} not found for deletion")
            raise HTTPException(status_code=404, detail="Map location not found")
        logger.info(f"Map location with ID {location_id} deleted successfully")
        return {"message": "Map location deleted successfully"}
