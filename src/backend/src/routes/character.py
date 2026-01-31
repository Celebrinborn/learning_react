from fastapi import APIRouter, HTTPException
from typing import List

from models.character import Character, CharacterCreate, CharacterUpdate
from storage.character import (
    create_character,
    get_character,
    get_all_characters,
    update_character,
    delete_character,
)

router = APIRouter(prefix="/api/characters", tags=["Characters"])

@router.post("", response_model=Character, status_code=201)
async def create_new_character(character: CharacterCreate):
    """Create a new character"""
    return create_character(character)

@router.get("", response_model=List[Character])
async def list_characters():
    """Get all characters"""
    return get_all_characters()

@router.get("/{character_id}", response_model=Character)
async def get_character_by_id(character_id: str):
    """Get a specific character by ID"""
    character = get_character(character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    return character

@router.put("/{character_id}", response_model=Character)
async def update_character_by_id(character_id: str, character_data: CharacterUpdate):
    """Update a character"""
    character = update_character(character_id, character_data)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    return character

@router.delete("/{character_id}")
async def delete_character_by_id(character_id: str):
    """Delete a character"""
    success = delete_character(character_id)
    if not success:
        raise HTTPException(status_code=404, detail="Character not found")
    return {"message": "Character deleted successfully"}
