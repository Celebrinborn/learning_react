"""Tests for character storage operations."""
import pytest
import json
from pathlib import Path
from unittest.mock import patch

from models.character import Character, CharacterCreate, CharacterUpdate
from storage import character as storage


class TestCharacterStorage:
    """Tests for character storage CRUD operations."""

    @pytest.fixture(autouse=True)
    def setup_storage_path(self, character_storage_path: Path, monkeypatch):
        """Mock the DATA_DIR to use a temporary directory."""
        monkeypatch.setattr(storage, "DATA_DIR", character_storage_path)

    def test_create_character(self):
        """Test creating a new character."""
        char_data = CharacterCreate(
            name="Test Character",
            race="Human",
            class_type="Fighter",
            level=1
        )

        result = storage.create_character(char_data)

        assert isinstance(result, Character)
        assert result.id is not None
        assert result.name == "Test Character"
        assert result.race == "Human"
        assert result.class_type == "Fighter"
        assert result.level == 1
        assert result.created_at is not None
        assert result.updated_at is not None

    def test_create_character_saves_to_disk(self):
        """Test that creating a character saves it to disk."""
        char_data = CharacterCreate(name="Saved Character")

        result = storage.create_character(char_data)
        file_path = storage._get_character_file_path(result.id)

        assert file_path.exists()

        # Verify file contents
        with open(file_path, 'r') as f:
            data = json.load(f)
            assert data["id"] == result.id
            assert data["name"] == "Saved Character"

    def test_get_character_exists(self):
        """Test retrieving an existing character."""
        char_data = CharacterCreate(name="Existing Character")
        created = storage.create_character(char_data)

        result = storage.get_character(created.id)

        assert result is not None
        assert result.id == created.id
        assert result.name == "Existing Character"

    def test_get_character_not_exists(self):
        """Test retrieving a non-existent character returns None."""
        result = storage.get_character("nonexistent-id")
        assert result is None

    def test_get_all_characters_empty(self):
        """Test getting all characters when none exist."""
        result = storage.get_all_characters()
        assert result == []

    def test_get_all_characters_multiple(self):
        """Test getting all characters when multiple exist."""
        names = ["Hero 1", "Hero 2", "Hero 3"]
        created_chars = []

        for name in names:
            char = storage.create_character(CharacterCreate(name=name))
            created_chars.append(char)

        result = storage.get_all_characters()

        assert len(result) == 3
        result_names = {char.name for char in result}
        assert result_names == set(names)

    def test_update_character_exists(self):
        """Test updating an existing character."""
        # Create a character
        char_data = CharacterCreate(name="Original Name", level=1)
        created = storage.create_character(char_data)

        # Update it
        update_data = CharacterUpdate(name="Updated Name", level=5)
        result = storage.update_character(created.id, update_data)

        assert result is not None
        assert result.id == created.id
        assert result.name == "Updated Name"
        assert result.level == 5
        assert result.updated_at > created.updated_at

    def test_update_character_partial(self):
        """Test updating only some fields of a character."""
        char_data = CharacterCreate(
            name="Hero",
            race="Elf",
            class_type="Wizard",
            level=3
        )
        created = storage.create_character(char_data)

        # Update only level
        update_data = CharacterUpdate(level=10)
        result = storage.update_character(created.id, update_data)

        assert result is not None
        assert result.name == "Hero"  # Unchanged
        assert result.race == "Elf"  # Unchanged
        assert result.class_type == "Wizard"  # Unchanged
        assert result.level == 10  # Updated

    def test_update_character_not_exists(self):
        """Test updating a non-existent character returns None."""
        update_data = CharacterUpdate(name="New Name")
        result = storage.update_character("nonexistent-id", update_data)

        assert result is None

    def test_update_character_persists_to_disk(self):
        """Test that updates are persisted to disk."""
        char_data = CharacterCreate(name="Before Update")
        created = storage.create_character(char_data)

        update_data = CharacterUpdate(name="After Update")
        storage.update_character(created.id, update_data)

        # Read directly from disk
        file_path = storage._get_character_file_path(created.id)
        with open(file_path, 'r') as f:
            data = json.load(f)
            assert data["name"] == "After Update"

    def test_delete_character_exists(self):
        """Test deleting an existing character."""
        char_data = CharacterCreate(name="To Be Deleted")
        created = storage.create_character(char_data)

        result = storage.delete_character(created.id)

        assert result is True
        assert storage.get_character(created.id) is None

        # Verify file is deleted
        file_path = storage._get_character_file_path(created.id)
        assert not file_path.exists()

    def test_delete_character_not_exists(self):
        """Test deleting a non-existent character returns False."""
        result = storage.delete_character("nonexistent-id")
        assert result is False

    def test_character_file_path_format(self):
        """Test that character file paths follow the expected format."""
        char_id = "test-123"
        file_path = storage._get_character_file_path(char_id)

        assert file_path.name == "test-123.json"
        assert file_path.parent.name == "characters"

    def test_load_all_characters_handles_corrupted_file(self, character_storage_path: Path):
        """Test that loading all characters handles corrupted JSON files gracefully."""
        # Create a valid character
        storage.create_character(CharacterCreate(name="Valid Character"))

        # Create a corrupted file
        corrupted_path = character_storage_path / "corrupted.json"
        corrupted_path.write_text("{ invalid json }")

        # Should still return the valid character
        result = storage.get_all_characters()

        assert len(result) == 1
        assert result[0].name == "Valid Character"

    def test_create_character_generates_unique_ids(self):
        """Test that each character gets a unique ID."""
        char1 = storage.create_character(CharacterCreate(name="Char 1"))
        char2 = storage.create_character(CharacterCreate(name="Char 2"))
        char3 = storage.create_character(CharacterCreate(name="Char 3"))

        assert char1.id != char2.id
        assert char2.id != char3.id
        assert char1.id != char3.id

    def test_create_character_with_stats(self):
        """Test creating a character with custom stats."""
        stats = {
            "strength": 18,
            "dexterity": 14,
            "constitution": 16,
            "intelligence": 10,
            "wisdom": 12,
            "charisma": 8
        }

        char_data = CharacterCreate(name="Barbarian", stats=stats)
        result = storage.create_character(char_data)

        assert result.stats == stats

        # Verify retrieval
        retrieved = storage.get_character(result.id)
        assert retrieved.stats == stats
