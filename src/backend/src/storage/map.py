import json
from typing import List, Optional
from datetime import datetime, timezone
import re

from interfaces.blob import IBlob
from models.map import MapLocation, MapLocationCreate, MapLocationUpdate
from telemetry import get_tracer


class MapStorage:
    """Storage service for map locations. Uses IBlobStorage for file operations."""

    def __init__(self, blob_storage: IBlob) -> None:
        self._storage = blob_storage

    def _sanitize_name(self, name: str) -> str:
        """Sanitize a name to be safe for use as a filename."""
        sanitized = re.sub(r'[^\w\s-]', '', name)
        sanitized = re.sub(r'[-\s]+', '_', sanitized)
        return sanitized.strip('_').lower()

    async def _name_exists(self, name: str, exclude_name: Optional[str] = None) -> bool:
        """Check if a location with this name already exists."""
        path = f"{self._sanitize_name(name)}.json"

        if exclude_name and self._sanitize_name(name) == self._sanitize_name(exclude_name):
            return False

        return await self._storage.exists(path)

    async def create_map_location(self, location_data: MapLocationCreate) -> MapLocation:
        """Create a new map location and save to storage."""
        tracer = get_tracer()
        with tracer.start_as_current_span("storage.create_map_location") as span:
            span.set_attribute("location.name", location_data.name)

            if await self._name_exists(location_data.name):
                raise ValueError(f"A location with the name '{location_data.name}' already exists")

            now = datetime.now(timezone.utc)
            sanitized_id = self._sanitize_name(location_data.name)
            span.set_attribute("location.id", sanitized_id)

            location = MapLocation(
                id=sanitized_id,
                name=location_data.name,
                description=location_data.description or "",
                latitude=location_data.latitude,
                longitude=location_data.longitude,
                map_id=location_data.map_id or "default",
                icon_type=location_data.icon_type or "other",
                created_at=now,
                updated_at=now
            )

            path = f"{sanitized_id}.json"
            data = json.dumps(location.model_dump(mode='json'), indent=2, default=str)
            await self._storage.write(path, data.encode('utf-8'))

            return location

    async def get_map_location(self, location_id: str) -> Optional[MapLocation]:
        """Get a map location by ID."""
        tracer = get_tracer()
        with tracer.start_as_current_span("storage.get_map_location") as span:
            span.set_attribute("location.id", location_id)
            path = f"{self._sanitize_name(location_id)}.json"

            if not await self._storage.exists(path):
                span.set_attribute("found", False)
                return None

            try:
                raw = await self._storage.read(path)
                data = json.loads(raw.decode('utf-8'))
                span.set_attribute("found", True)
                return MapLocation(**data)
            except Exception as e:
                print(f"Error loading location {location_id}: {e}")
                span.set_attribute("error", str(e))
                return None

    async def get_all_map_locations(self, map_id: Optional[str] = None) -> List[MapLocation]:
        """Get all map locations, optionally filtered by map_id."""
        tracer = get_tracer()
        with tracer.start_as_current_span("storage.get_all_map_locations") as span:
            if map_id:
                span.set_attribute("filter.map_id", map_id)

            locations: List[MapLocation] = []
            all_paths = await self._storage.list()
            json_paths = [p for p in all_paths if p.endswith('.json')]

            for path in json_paths:
                try:
                    raw = await self._storage.read(path)
                    data = json.loads(raw.decode('utf-8'))
                    locations.append(MapLocation(**data))
                except Exception as e:
                    print(f"Error loading {path}: {e}")

            if map_id:
                locations = [loc for loc in locations if loc.map_id == map_id]

            span.set_attribute("count", len(locations))
            return locations

    async def update_map_location(self, location_id: str, location_data: MapLocationUpdate) -> Optional[MapLocation]:
        """Update a map location."""
        tracer = get_tracer()
        with tracer.start_as_current_span("storage.update_map_location") as span:
            span.set_attribute("location.id", location_id)
            existing_location = await self.get_map_location(location_id)

            if not existing_location:
                span.set_attribute("found", False)
                return None

            span.set_attribute("found", True)
            if location_data.name and location_data.name != existing_location.name:
                if await self._name_exists(location_data.name, exclude_name=existing_location.name):
                    raise ValueError(f"A location with the name '{location_data.name}' already exists")

            old_path = f"{self._sanitize_name(existing_location.name)}.json"

            updated_location = MapLocation(
                id=self._sanitize_name(location_data.name if location_data.name else existing_location.name),
                name=location_data.name if location_data.name else existing_location.name,
                description=location_data.description if location_data.description is not None else existing_location.description,
                latitude=location_data.latitude if location_data.latitude is not None else existing_location.latitude,
                longitude=location_data.longitude if location_data.longitude is not None else existing_location.longitude,
                map_id=location_data.map_id if location_data.map_id else existing_location.map_id,
                icon_type=location_data.icon_type if location_data.icon_type else existing_location.icon_type,
                created_at=existing_location.created_at,
                updated_at=datetime.now(timezone.utc)
            )

            new_path = f"{self._sanitize_name(updated_location.name)}.json"

            if old_path != new_path:
                try:
                    await self._storage.delete(old_path)
                except FileNotFoundError:
                    pass

            data = json.dumps(updated_location.model_dump(mode='json'), indent=2, default=str)
            await self._storage.write(new_path, data.encode('utf-8'))

            return updated_location

    async def delete_map_location(self, location_id: str) -> bool:
        """Delete a map location."""
        tracer = get_tracer()
        with tracer.start_as_current_span("storage.delete_map_location") as span:
            span.set_attribute("location.id", location_id)
            path = f"{self._sanitize_name(location_id)}.json"

            if not await self._storage.exists(path):
                span.set_attribute("success", False)
                return False

            try:
                await self._storage.delete(path)
                span.set_attribute("success", True)
                return True
            except Exception as e:
                print(f"Error deleting location {location_id}: {e}")
                span.set_attribute("success", False)
                span.set_attribute("error", str(e))
                return False
