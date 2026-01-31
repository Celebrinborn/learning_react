import json
from pathlib import Path
from typing import List, Optional
from datetime import datetime
import uuid

from dnd_backend.models.character import Character, CharacterCreate, CharacterUpdate

# Get the data directory path (relative to project root)
DATA_DIR = Path(__file__).parent.parent.parent.parent / "data" / "characters"
DATA_DIR.mkdir(parents=True, exist_ok=True)

def _get_character_file_path(character_id: str) -> Path:
    """Get the file path for a character"""
    return DATA_DIR / f"{character_id}.json"

def _load_all_characters() -> List[Character]:
    """Load all characters from disk"""
    characters = []
    if not DATA_DIR.exists():
        return characters
    
    for file_path in DATA_DIR.glob("*.json"):
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                characters.append(Character(**data))
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
    
    return characters

def create_character(character_data: CharacterCreate) -> Character:
    """Create a new character and save to disk"""
    character_id = str(uuid.uuid4())
    now = datetime.utcnow()
    
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
    
    # Save to disk
    file_path = _get_character_file_path(character_id)
    with open(file_path, 'w') as f:
        json.dump(character.model_dump(mode='json'), f, indent=2, default=str)
    
    return character

def get_character(character_id: str) -> Optional[Character]:
    """Get a character by ID"""
    file_path = _get_character_file_path(character_id)
    
    if not file_path.exists():
        return None
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            return Character(**data)
    except Exception as e:
        print(f"Error loading character {character_id}: {e}")
        return None

def get_all_characters() -> List[Character]:
    """Get all characters"""
    return _load_all_characters()

def update_character(character_id: str, character_data: CharacterUpdate) -> Optional[Character]:
    """Update a character"""
    existing_character = get_character(character_id)
    
    if not existing_character:
        return None
    
    # Update fields
    update_dict = character_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(existing_character, field, value)
    
    existing_character.updated_at = datetime.utcnow()
    
    # Save to disk
    file_path = _get_character_file_path(character_id)
    with open(file_path, 'w') as f:
        json.dump(existing_character.model_dump(mode='json'), f, indent=2, default=str)
    
    return existing_character

def delete_character(character_id: str) -> bool:
    """Delete a character"""
    file_path = _get_character_file_path(character_id)
    
    if not file_path.exists():
        return False
    
    try:
        file_path.unlink()
        return True
    except Exception as e:
        print(f"Error deleting character {character_id}: {e}")
        return False
