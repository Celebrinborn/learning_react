from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class MapLocationCreate(BaseModel):
    """Model for creating a new map location - only required fields"""
    name: str
    latitude: float
    longitude: float
    description: Optional[str] = Field(default="")
    map_id: Optional[str] = Field(default="default")
    icon_type: Optional[str] = Field(default="other")

class MapLocationUpdate(BaseModel):
    """Model for updating a map location - all fields optional"""
    name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    description: Optional[str] = None
    map_id: Optional[str] = None
    icon_type: Optional[str] = None

class MapLocation(BaseModel):
    """Model for a map location with all fields including timestamps"""
    id: str
    name: str
    latitude: float
    longitude: float
    description: str = Field(default="")  # Can be empty string
    map_id: str = Field(default="default")  # ID of the parent map
    icon_type: str = Field(default="other")
    created_at: datetime
    updated_at: datetime
