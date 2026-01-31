"""Tests for data models."""
import pytest
from datetime import datetime
from pydantic import ValidationError

from models.character import Character, CharacterCreate, CharacterUpdate


class TestCharacterModels:
    """Tests for Character model classes."""

    def test_character_create_minimal(self):
        """Test creating a character with minimal required fields."""
        char = CharacterCreate(name="Gandalf")

        assert char.name == "Gandalf"
        assert char.race is None
        assert char.class_type is None
        assert char.level == 1  # Default value
        assert char.stats is None

    def test_character_create_full(self):
        """Test creating a character with all fields."""
        stats = {
            "strength": 18,
            "dexterity": 14,
            "constitution": 16,
            "intelligence": 10,
            "wisdom": 12,
            "charisma": 8
        }

        char = CharacterCreate(
            name="Conan",
            race="Human",
            class_type="Barbarian",
            level=5,
            stats=stats
        )

        assert char.name == "Conan"
        assert char.race == "Human"
        assert char.class_type == "Barbarian"
        assert char.level == 5
        assert char.stats == stats

    def test_character_create_validation_error_no_name(self):
        """Test that creating a character without a name raises ValidationError."""
        with pytest.raises(ValidationError):
            CharacterCreate()

    def test_character_full_model(self):
        """Test the full Character model with all fields."""
        now = datetime.utcnow()
        stats = {"strength": 10}

        char = Character(
            id="123e4567-e89b-12d3-a456-426614174000",
            name="Bilbo",
            race="Halfling",
            class_type="Rogue",
            level=3,
            stats=stats,
            created_at=now,
            updated_at=now
        )

        assert char.id == "123e4567-e89b-12d3-a456-426614174000"
        assert char.name == "Bilbo"
        assert char.race == "Halfling"
        assert char.class_type == "Rogue"
        assert char.level == 3
        assert char.stats == stats
        assert char.created_at == now
        assert char.updated_at == now

    def test_character_update_empty(self):
        """Test creating an update with no fields set."""
        update = CharacterUpdate()

        assert update.name is None
        assert update.race is None
        assert update.class_type is None
        assert update.level is None
        assert update.stats is None

    def test_character_update_partial(self):
        """Test updating only specific fields."""
        update = CharacterUpdate(name="New Name", level=10)

        assert update.name == "New Name"
        assert update.level == 10
        assert update.race is None
        assert update.class_type is None

    def test_character_model_dump(self):
        """Test serialization of Character model to dict."""
        char = Character(
            id="test-id",
            name="Test Hero",
            race="Elf",
            class_type="Wizard",
            level=7
        )

        data = char.model_dump()

        assert isinstance(data, dict)
        assert data["id"] == "test-id"
        assert data["name"] == "Test Hero"
        assert data["race"] == "Elf"
        assert data["class_type"] == "Wizard"
        assert data["level"] == 7

    def test_character_from_dict(self):
        """Test creating a Character from a dictionary."""
        data = {
            "id": "abc-123",
            "name": "Aragorn",
            "race": "Human",
            "class_type": "Ranger",
            "level": 8,
            "stats": {"strength": 16},
            "created_at": "2026-01-30T12:00:00",
            "updated_at": "2026-01-30T12:00:00"
        }

        char = Character(**data)

        assert char.id == "abc-123"
        assert char.name == "Aragorn"
        assert char.race == "Human"

    def test_character_stats_can_be_dict(self):
        """Test that stats field accepts arbitrary dictionaries."""
        custom_stats = {
            "hp": 50,
            "ac": 18,
            "custom_field": "value",
            "nested": {"data": 123}
        }

        char = CharacterCreate(name="Test", stats=custom_stats)

        assert char.stats == custom_stats
        assert char.stats["nested"]["data"] == 123
