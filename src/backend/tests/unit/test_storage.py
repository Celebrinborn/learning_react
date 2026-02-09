"""Tests for character storage operations."""
import pytest
import json
from pathlib import Path

from models.character import Character, CharacterCreate, CharacterUpdate
from storage.character import CharacterStorage
from providers.local_file_blob import LocalFileBlobProvider


class TestCharacterStorage:
    """Tests for character storage CRUD operations."""

    @pytest.fixture(autouse=True)
    def setup_storage(self, character_storage_path: Path):
        """Create a CharacterStorage backed by a temp directory."""
        blob = LocalFileBlobProvider(character_storage_path)
        self.storage = CharacterStorage(blob)
        self.storage_path = character_storage_path

    @pytest.mark.asyncio
    async def test_create_character(self):
        """Test creating a new character."""
        char_data = CharacterCreate(
            name="Test Character",
            race="Human",
            class_type="Fighter",
            level=1
        )

        result = await self.storage.create_character(char_data)

        assert isinstance(result, Character)
        assert result.id is not None
        assert result.name == "Test Character"
        assert result.race == "Human"
        assert result.class_type == "Fighter"
        assert result.level == 1
        assert result.created_at is not None
        assert result.updated_at is not None

    @pytest.mark.asyncio
    async def test_create_character_saves_to_disk(self):
        """Test that creating a character saves it to storage."""
        char_data = CharacterCreate(name="Saved Character")

        result = await self.storage.create_character(char_data)
        exists = await self.storage._storage.exists(f"{result.id}.json")

        assert exists

        # Verify contents via read
        raw = await self.storage._storage.read(f"{result.id}.json")
        data = json.loads(raw.decode('utf-8'))
        assert data["id"] == result.id
        assert data["name"] == "Saved Character"

    @pytest.mark.asyncio
    async def test_get_character_exists(self):
        """Test retrieving an existing character."""
        char_data = CharacterCreate(name="Existing Character")
        created = await self.storage.create_character(char_data)

        result = await self.storage.get_character(created.id)

        assert result is not None
        assert result.id == created.id
        assert result.name == "Existing Character"

    @pytest.mark.asyncio
    async def test_get_character_not_exists(self):
        """Test retrieving a non-existent character returns None."""
        result = await self.storage.get_character("nonexistent-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_all_characters_empty(self):
        """Test getting all characters when none exist."""
        result = await self.storage.get_all_characters()
        assert result == []

    @pytest.mark.asyncio
    async def test_get_all_characters_multiple(self):
        """Test getting all characters when multiple exist."""
        names = ["Hero 1", "Hero 2", "Hero 3"]

        for name in names:
            await self.storage.create_character(CharacterCreate(name=name))

        result = await self.storage.get_all_characters()

        assert len(result) == 3
        result_names = {char.name for char in result}
        assert result_names == set(names)

    @pytest.mark.asyncio
    async def test_update_character_exists(self):
        """Test updating an existing character."""
        char_data = CharacterCreate(name="Original Name", level=1)
        created = await self.storage.create_character(char_data)

        update_data = CharacterUpdate(name="Updated Name", level=5)
        result = await self.storage.update_character(created.id, update_data)

        assert result is not None
        assert result.id == created.id
        assert result.name == "Updated Name"
        assert result.level == 5
        assert result.updated_at > created.updated_at

    @pytest.mark.asyncio
    async def test_update_character_partial(self):
        """Test updating only some fields of a character."""
        char_data = CharacterCreate(
            name="Hero",
            race="Elf",
            class_type="Wizard",
            level=3
        )
        created = await self.storage.create_character(char_data)

        update_data = CharacterUpdate(level=10)
        result = await self.storage.update_character(created.id, update_data)

        assert result is not None
        assert result.name == "Hero"  # Unchanged
        assert result.race == "Elf"  # Unchanged
        assert result.class_type == "Wizard"  # Unchanged
        assert result.level == 10  # Updated

    @pytest.mark.asyncio
    async def test_update_character_not_exists(self):
        """Test updating a non-existent character returns None."""
        update_data = CharacterUpdate(name="New Name")
        result = await self.storage.update_character("nonexistent-id", update_data)

        assert result is None

    @pytest.mark.asyncio
    async def test_update_character_persists_to_disk(self):
        """Test that updates are persisted to storage."""
        char_data = CharacterCreate(name="Before Update")
        created = await self.storage.create_character(char_data)

        update_data = CharacterUpdate(name="After Update")
        await self.storage.update_character(created.id, update_data)

        # Read directly from storage
        raw = await self.storage._storage.read(f"{created.id}.json")
        data = json.loads(raw.decode('utf-8'))
        assert data["name"] == "After Update"

    @pytest.mark.asyncio
    async def test_delete_character_exists(self):
        """Test deleting an existing character."""
        char_data = CharacterCreate(name="To Be Deleted")
        created = await self.storage.create_character(char_data)

        result = await self.storage.delete_character(created.id)

        assert result is True
        assert await self.storage.get_character(created.id) is None

        # Verify blob is deleted
        exists = await self.storage._storage.exists(f"{created.id}.json")
        assert not exists

    @pytest.mark.asyncio
    async def test_delete_character_not_exists(self):
        """Test deleting a non-existent character returns False."""
        result = await self.storage.delete_character("nonexistent-id")
        assert result is False

    @pytest.mark.asyncio
    async def test_load_all_characters_handles_corrupted_file(self):
        """Test that loading all characters handles corrupted JSON files gracefully."""
        await self.storage.create_character(CharacterCreate(name="Valid Character"))

        # Create a corrupted file directly on disk
        corrupted_path = self.storage_path / "corrupted.json"
        corrupted_path.write_text("{ invalid json }")

        result = await self.storage.get_all_characters()

        assert len(result) == 1
        assert result[0].name == "Valid Character"

    @pytest.mark.asyncio
    async def test_create_character_generates_unique_ids(self):
        """Test that each character gets a unique ID."""
        char1 = await self.storage.create_character(CharacterCreate(name="Char 1"))
        char2 = await self.storage.create_character(CharacterCreate(name="Char 2"))
        char3 = await self.storage.create_character(CharacterCreate(name="Char 3"))

        assert char1.id != char2.id
        assert char2.id != char3.id
        assert char1.id != char3.id

    @pytest.mark.asyncio
    async def test_create_character_with_stats(self):
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
        result = await self.storage.create_character(char_data)

        assert result.stats == stats

        # Verify retrieval
        retrieved = await self.storage.get_character(result.id)
        assert retrieved is not None
        assert retrieved.stats == stats
