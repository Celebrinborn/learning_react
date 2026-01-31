from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class MapLocation(BaseModel):
    """Model for a map location"""
    id: str
    name: str
    description: Optional[str] = None
    latitude: float
    longitude: float
    map_id: Optional[str] = None
    icon_type: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class MapLocationCreate(BaseModel):
    """Model for creating a map location"""
    name: str
    description: Optional[str] = None
    latitude: float
    longitude: float
    map_id: Optional[str] = None
    icon_type: Optional[str] = None

class MapLocationUpdate(BaseModel):
    """Model for updating a map location"""
    name: Optional[str] = None
    description: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    map_id: Optional[str] = None
    icon_type: Optional[str] = None
