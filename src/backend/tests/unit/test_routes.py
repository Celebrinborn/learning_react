"""Tests for FastAPI character routes."""
import pytest
from fastapi.testclient import TestClient
from pathlib import Path

from models.character import CharacterCreate, CharacterUpdate
from storage.character import CharacterStorage
from providers.local_file_blob import LocalFileBlobProvider
from routes import character as character_route_module
from routes.character import router
from fastapi import FastAPI


@pytest.fixture
def app():
    """Create a FastAPI app instance for testing."""
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app: FastAPI):
    """Create a test client."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def setup_storage(character_storage_path: Path, monkeypatch):
    """Inject a CharacterStorage backed by tmp_path."""
    blob = LocalFileBlobProvider(character_storage_path)
    test_storage = CharacterStorage(blob)
    monkeypatch.setattr(character_route_module, "_character_storage", test_storage)


class TestCharacterRoutes:
    """Tests for character API routes."""

    def test_create_character_success(self, client: TestClient):
        """Test creating a character via API."""
        character_data = {
            "name": "API Hero",
            "race": "Dwarf",
            "class_type": "Cleric",
            "level": 2
        }

        response = client.post("/api/characters", json=character_data)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "API Hero"
        assert data["race"] == "Dwarf"
        assert data["class_type"] == "Cleric"
        assert data["level"] == 2
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_character_minimal(self, client: TestClient):
        """Test creating a character with only required fields."""
        character_data = {"name": "Minimal Hero"}

        response = client.post("/api/characters", json=character_data)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Minimal Hero"
        assert data["level"] == 1  # Default value

    def test_create_character_missing_name(self, client: TestClient):
        """Test that creating a character without a name fails."""
        character_data = {"race": "Elf"}

        response = client.post("/api/characters", json=character_data)

        assert response.status_code == 422  # Validation error

    def test_list_characters_empty(self, client: TestClient):
        """Test listing characters when none exist."""
        response = client.get("/api/characters")

        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_list_characters_multiple(self, client: TestClient):
        """Test listing multiple characters."""
        # Create characters
        names = ["Hero A", "Hero B", "Hero C"]
        for name in names:
            client.post("/api/characters", json={"name": name})

        response = client.get("/api/characters")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        result_names = {char["name"] for char in data}
        assert result_names == set(names)

    def test_get_character_by_id_exists(self, client: TestClient):
        """Test getting a specific character by ID."""
        # Create a character
        create_response = client.post(
            "/api/characters",
            json={"name": "Specific Hero"}
        )
        character_id = create_response.json()["id"]

        # Get the character
        response = client.get(f"/api/characters/{character_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == character_id
        assert data["name"] == "Specific Hero"

    def test_get_character_by_id_not_exists(self, client: TestClient):
        """Test getting a non-existent character returns 404."""
        response = client.get("/api/characters/nonexistent-id")

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_update_character_success(self, client: TestClient):
        """Test updating a character via API."""
        # Create a character
        create_response = client.post(
            "/api/characters",
            json={"name": "Original", "level": 1}
        )
        character_id = create_response.json()["id"]

        # Update the character
        update_data = {"name": "Updated", "level": 5}
        response = client.put(
            f"/api/characters/{character_id}",
            json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == character_id
        assert data["name"] == "Updated"
        assert data["level"] == 5

    def test_update_character_partial(self, client: TestClient):
        """Test partially updating a character."""
        # Create a character
        create_response = client.post(
            "/api/characters",
            json={"name": "Hero", "race": "Elf", "level": 3}
        )
        character_id = create_response.json()["id"]

        # Update only level
        update_data = {"level": 10}
        response = client.put(
            f"/api/characters/{character_id}",
            json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Hero"  # Unchanged
        assert data["race"] == "Elf"  # Unchanged
        assert data["level"] == 10  # Updated

    def test_update_character_not_exists(self, client: TestClient):
        """Test updating a non-existent character returns 404."""
        update_data = {"name": "New Name"}
        response = client.put(
            "/api/characters/nonexistent-id",
            json=update_data
        )

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_delete_character_success(self, client: TestClient):
        """Test deleting a character via API."""
        # Create a character
        create_response = client.post(
            "/api/characters",
            json={"name": "To Delete"}
        )
        character_id = create_response.json()["id"]

        # Delete the character
        response = client.delete(f"/api/characters/{character_id}")

        assert response.status_code == 200
        data = response.json()
        assert "deleted successfully" in data["message"].lower()

        # Verify it's deleted
        get_response = client.get(f"/api/characters/{character_id}")
        assert get_response.status_code == 404

    def test_delete_character_not_exists(self, client: TestClient):
        """Test deleting a non-existent character returns 404."""
        response = client.delete("/api/characters/nonexistent-id")

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_create_character_with_stats(self, client: TestClient):
        """Test creating a character with custom stats."""
        stats = {
            "strength": 16,
            "dexterity": 12,
            "constitution": 14,
            "intelligence": 10,
            "wisdom": 13,
            "charisma": 15
        }

        character_data = {
            "name": "Stat Hero",
            "stats": stats
        }

        response = client.post("/api/characters", json=character_data)

        assert response.status_code == 201
        data = response.json()
        assert data["stats"] == stats

    def test_end_to_end_crud_workflow(self, client: TestClient):
        """Test a complete CRUD workflow."""
        # CREATE
        create_response = client.post(
            "/api/characters",
            json={"name": "Workflow Hero", "level": 1}
        )
        assert create_response.status_code == 201
        character_id = create_response.json()["id"]

        # READ (single)
        read_response = client.get(f"/api/characters/{character_id}")
        assert read_response.status_code == 200
        assert read_response.json()["name"] == "Workflow Hero"

        # UPDATE
        update_response = client.put(
            f"/api/characters/{character_id}",
            json={"level": 10}
        )
        assert update_response.status_code == 200
        assert update_response.json()["level"] == 10

        # READ (list)
        list_response = client.get("/api/characters")
        assert list_response.status_code == 200
        assert len(list_response.json()) >= 1

        # DELETE
        delete_response = client.delete(f"/api/characters/{character_id}")
        assert delete_response.status_code == 200

        # Verify deletion
        final_read = client.get(f"/api/characters/{character_id}")
        assert final_read.status_code == 404
