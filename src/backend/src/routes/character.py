from fastapi import APIRouter, HTTPException
from typing import List
from opentelemetry import trace

from models.character import Character, CharacterCreate, CharacterUpdate
from storage.character import CharacterStorage
from builder import AppBuilder
from telemetry import get_tracer

router = APIRouter(prefix="/api/characters", tags=["Characters"])

_builder = AppBuilder()
_character_storage = CharacterStorage(_builder.build_character_blob_storage())

@router.post("", response_model=Character, status_code=201)
async def create_new_character(character: CharacterCreate):
    """Create a new character"""
    tracer = get_tracer()
    with tracer.start_as_current_span("create_character_handler") as span:
        span.set_attribute("character.name", character.name)
        return await _character_storage.create_character(character)

@router.get("", response_model=List[Character])
async def list_characters():
    """Get all characters"""
    tracer = get_tracer()
    with tracer.start_as_current_span("list_characters_handler"):
        return await _character_storage.get_all_characters()

@router.get("/{character_id}", response_model=Character)
async def get_character_by_id(character_id: str):
    """Get a specific character by ID"""
    tracer = get_tracer()
    with tracer.start_as_current_span("get_character_handler") as span:
        span.set_attribute("character.id", character_id)
        character = await _character_storage.get_character(character_id)
        if not character:
            span.set_status(trace.Status(trace.StatusCode.ERROR, "Character not found"))
            raise HTTPException(status_code=404, detail="Character not found")
        return character

@router.put("/{character_id}", response_model=Character)
async def update_character_by_id(character_id: str, character_data: CharacterUpdate):
    """Update a character"""
    tracer = get_tracer()
    with tracer.start_as_current_span("update_character_handler") as span:
        span.set_attribute("character.id", character_id)
        character = await _character_storage.update_character(character_id, character_data)
        if not character:
            span.set_status(trace.Status(trace.StatusCode.ERROR, "Character not found"))
            raise HTTPException(status_code=404, detail="Character not found")
        return character

@router.delete("/{character_id}")
async def delete_character_by_id(character_id: str):
    """Delete a character"""
    tracer = get_tracer()
    with tracer.start_as_current_span("delete_character_handler") as span:
        span.set_attribute("character.id", character_id)
        success = await _character_storage.delete_character(character_id)
        if not success:
            span.set_status(trace.Status(trace.StatusCode.ERROR, "Character not found"))
            raise HTTPException(status_code=404, detail="Character not found")
        return {"message": "Character deleted successfully"}
