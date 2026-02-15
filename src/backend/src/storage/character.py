import json
from typing import List, Optional
from datetime import datetime, timezone
import uuid

from interfaces.blob import IBlob
from models.character import Character, CharacterCreate, CharacterUpdate
from telemetry import get_tracer


class CharacterStorage:
    """Storage service for characters. Uses IBlobStorage for file operations."""

    def __init__(self, blob_storage: IBlob) -> None:
        self._storage = blob_storage

    async def create_character(self, character_data: CharacterCreate) -> Character:
        """Create a new character and save to storage."""
        tracer = get_tracer()
        with tracer.start_as_current_span("storage.create_character") as span:
            character_id = str(uuid.uuid4())
            span.set_attribute("character.id", character_id)
            span.set_attribute("character.name", character_data.name)
            now = datetime.now(timezone.utc)

            character = Character(
                id=character_id,
                name=character_data.name,
                race=character_data.race,
                class_type=character_data.class_type,
                level=character_data.level,
                stats=character_data.stats,
                created_at=now,
                updated_at=now
            )

            path = f"{character_id}.json"
            data = json.dumps(character.model_dump(mode='json'), indent=2, default=str)
            await self._storage.write(path, data.encode('utf-8'))

            return character

    async def get_character(self, character_id: str) -> Optional[Character]:
        """Get a character by ID."""
        tracer = get_tracer()
        with tracer.start_as_current_span("storage.get_character") as span:
            span.set_attribute("character.id", character_id)
            path = f"{character_id}.json"

            if not await self._storage.exists(path):
                span.set_attribute("found", False)
                return None

            try:
                raw = await self._storage.read(path)
                data = json.loads(raw.decode('utf-8'))
                span.set_attribute("found", True)
                return Character(**data)
            except Exception as e:
                print(f"Error loading character {character_id}: {e}")
                span.set_attribute("error", str(e))
                return None

    async def get_all_characters(self) -> List[Character]:
        """Get all characters."""
        tracer = get_tracer()
        with tracer.start_as_current_span("storage.get_all_characters") as span:
            characters: List[Character] = []
            all_paths = await self._storage.list()
            json_paths = [p for p in all_paths if p.endswith('.json')]

            for path in json_paths:
                try:
                    raw = await self._storage.read(path)
                    data = json.loads(raw.decode('utf-8'))
                    characters.append(Character(**data))
                except Exception as e:
                    print(f"Error loading {path}: {e}")

            span.set_attribute("count", len(characters))
            return characters

    async def update_character(self, character_id: str, character_data: CharacterUpdate) -> Optional[Character]:
        """Update a character."""
        tracer = get_tracer()
        with tracer.start_as_current_span("storage.update_character") as span:
            span.set_attribute("character.id", character_id)
            existing_character = await self.get_character(character_id)

            if not existing_character:
                span.set_attribute("found", False)
                return None

            span.set_attribute("found", True)
            update_dict = character_data.model_dump(exclude_unset=True)
            for field, value in update_dict.items():
                setattr(existing_character, field, value)

            existing_character.updated_at = datetime.now(timezone.utc)

            path = f"{character_id}.json"
            data = json.dumps(existing_character.model_dump(mode='json'), indent=2, default=str)
            await self._storage.write(path, data.encode('utf-8'))

            return existing_character

    async def delete_character(self, character_id: str) -> bool:
        """Delete a character."""
        tracer = get_tracer()
        with tracer.start_as_current_span("storage.delete_character") as span:
            span.set_attribute("character.id", character_id)
            path = f"{character_id}.json"

            if not await self._storage.exists(path):
                span.set_attribute("success", False)
                return False

            try:
                await self._storage.delete(path)
                span.set_attribute("success", True)
                return True
            except Exception as e:
                print(f"Error deleting character {character_id}: {e}")
                span.set_attribute("success", False)
                span.set_attribute("error", str(e))
                return False
