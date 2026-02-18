from fastapi import APIRouter, HTTPException
from typing import List

from models.character import Character, CharacterCreate, CharacterUpdate
from storage.character import CharacterStorage
from builder import AppBuilder

router = APIRouter(prefix="/api/characters", tags=["Characters"])

_builder = AppBuilder()
_character_storage = CharacterStorage(_builder.build_character_blob_storage())

@router.post("", response_model=Character, status_code=201)
async def create_new_character(character: CharacterCreate):
    """Create a new character"""
    return await _character_storage.create_character(character)

@router.get("", response_model=List[Character])
async def list_characters():
    """Get all characters"""
    return await _character_storage.get_all_characters()

@router.get("/{character_id}", response_model=Character)
async def get_character_by_id(character_id: str):
    """Get a specific character by ID"""
    character = await _character_storage.get_character(character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    return character

@router.put("/{character_id}", response_model=Character)
async def update_character_by_id(character_id: str, character_data: CharacterUpdate):
    """Update a character"""
    character = await _character_storage.update_character(character_id, character_data)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    return character

@router.delete("/{character_id}")
async def delete_character_by_id(character_id: str):
    """Delete a character"""
    success = await _character_storage.delete_character(character_id)
    if not success:
        raise HTTPException(status_code=404, detail="Character not found")
    return {"message": "Character deleted successfully"}
