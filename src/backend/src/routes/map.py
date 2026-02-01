from fastapi import APIRouter, HTTPException
from typing import Optional, List
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

router = APIRouter(prefix="/api/map-locations", tags=["Map Locations"])

@router.post("", response_model=MapLocation, status_code=201)
async def create_location(location: MapLocationCreate):
    """Create a new map location"""
    tracer = get_tracer()
    with tracer.start_as_current_span("create_map_location_handler") as span:
        span.set_attribute("location.name", location.name)
        try:
            return create_map_location(location)
        except ValueError as e:
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
            raise HTTPException(status_code=400, detail=str(e))

@router.get("", response_model=List[MapLocation])
async def list_locations(map_id: Optional[str] = None):
    """Get all map locations, optionally filtered by map_id"""
    tracer = get_tracer()
    with tracer.start_as_current_span("list_map_locations_handler") as span:
        if map_id:
            span.set_attribute("filter.map_id", map_id)
        return get_all_map_locations(map_id=map_id)

@router.get("/{location_id}", response_model=MapLocation)
async def get_location(location_id: str):
    """Get a specific map location by ID"""
    tracer = get_tracer()
    with tracer.start_as_current_span("get_map_location_handler") as span:
        span.set_attribute("location.id", location_id)
        location = get_map_location(location_id)
        if not location:
            span.set_status(trace.Status(trace.StatusCode.ERROR, "Map location not found"))
            raise HTTPException(status_code=404, detail="Map location not found")
        return location

@router.put("/{location_id}", response_model=MapLocation)
async def update_location(location_id: str, location_data: MapLocationUpdate):
    """Update a map location"""
    tracer = get_tracer()
    with tracer.start_as_current_span("update_map_location_handler") as span:
        span.set_attribute("location.id", location_id)
        try:
            location = update_map_location(location_id, location_data)
            if not location:
                span.set_status(trace.Status(trace.StatusCode.ERROR, "Map location not found"))
                raise HTTPException(status_code=404, detail="Map location not found")
            return location
        except ValueError as e:
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
            raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{location_id}")
async def delete_location(location_id: str):
    """Delete a map location"""
    tracer = get_tracer()
    with tracer.start_as_current_span("delete_map_location_handler") as span:
        span.set_attribute("location.id", location_id)
        success = delete_map_location(location_id)
        if not success:
            span.set_status(trace.Status(trace.StatusCode.ERROR, "Map location not found"))
            raise HTTPException(status_code=404, detail="Map location not found")
        return {"message": "Map location deleted successfully"}
