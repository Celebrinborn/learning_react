from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class Character(BaseModel):
    """Model for a character"""
    id: str
    name: str
    race: Optional[str] = None
    class_type: Optional[str] = None
    level: Optional[int] = 1
    stats: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class CharacterCreate(BaseModel):
    """Model for creating a character"""
    name: str
    race: Optional[str] = None
    class_type: Optional[str] = None
    level: Optional[int] = 1
    stats: Optional[Dict[str, Any]] = None

class CharacterUpdate(BaseModel):
    """Model for updating a character"""
    name: Optional[str] = None
    race: Optional[str] = None
    class_type: Optional[str] = None
    level: Optional[int] = None
    stats: Optional[Dict[str, Any]] = None
