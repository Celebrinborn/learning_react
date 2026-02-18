from fastapi import APIRouter, HTTPException
from typing import Optional, List
import logging
from opentelemetry import trace

from models.map import MapLocation, MapLocationCreate, MapLocationUpdate
from storage.map import MapStorage
from builder import AppBuilder
from telemetry import get_tracer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/map-locations", tags=["Map Locations"])

_builder = AppBuilder()
_map_storage = MapStorage(_builder.build_map_blob_storage())


@router.post("", response_model=MapLocation, status_code=201)
async def create_location(location: MapLocationCreate):
    """Create a new map location"""
    logger.info(f"Creating map location: {location.name}")
    tracer = get_tracer()
    with tracer.start_as_current_span("create_map_location_handler") as span:
        span.set_attribute("location.name", location.name)
        try:
            return await _map_storage.create_map_location(location)
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
        locations: list[MapLocation] = await _map_storage.get_all_map_locations(map_id=map_id)
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
        location = await _map_storage.get_map_location(location_id)
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
            location = await _map_storage.update_map_location(location_id, location_data)
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
        success = await _map_storage.delete_map_location(location_id)
        if not success:
            span.set_status(
                trace.Status(trace.StatusCode.ERROR, "Map location not found")
            )
            logger.warning(f"Map location with ID {location_id} not found for deletion")
            raise HTTPException(status_code=404, detail="Map location not found")
        logger.info(f"Map location with ID {location_id} deleted successfully")
        return {"message": "Map location deleted successfully"}
