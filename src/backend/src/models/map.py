from pydantic import BaseModel
from datetime import datetime

class MapLocation(BaseModel):
    """Model for a map location"""
    id: str
    name: str
    description: str  # Can be empty string, but not none
    latitude: float
    longitude: float
    map_id: str  # ID of the parent map (for when there are multiple maps)
    icon_type: str
    created_at: datetime
    updated_at: datetime
