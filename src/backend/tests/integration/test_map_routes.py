"""Integration tests for map location API routes."""
import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from pathlib import Path

from routes.map import router
from storage import map as map_storage


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


@pytest.fixture
def map_storage_path(tmp_path: Path) -> Path:
    """Create a temporary directory for map storage."""
    storage_dir = tmp_path / "maps"
    storage_dir.mkdir(parents=True, exist_ok=True)
    return storage_dir


@pytest.fixture(autouse=True)
def setup_storage_path(map_storage_path: Path, monkeypatch):
    """Mock the DATA_DIR to use a temporary directory."""
    monkeypatch.setattr(map_storage, "DATA_DIR", map_storage_path)


class TestMapLocationRoutes:
    """Integration tests for map location API routes."""

    def test_create_location_minimal_fields(self, client: TestClient):
        """Test creating a map location with only required fields."""
        # This simulates what the frontend sends
        location_data = {
            "name": "Haden",
            "latitude": 61.238051,
            "longitude": 7.712204,
        }

        response = client.post("/api/map-locations", json=location_data)

        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.text}")

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Haden"
        assert data["latitude"] == 61.238051
        assert data["longitude"] == 7.712204
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_location_with_description(self, client: TestClient):
        """Test creating a location with description."""
        location_data = {
            "name": "Mountain Village",
            "description": "A village in the mountains",
            "latitude": 61.0,
            "longitude": 7.0,
        }

        response = client.post("/api/map-locations", json=location_data)

        assert response.status_code == 201
        data = response.json()
        assert data["description"] == "A village in the mountains"

    def test_create_location_with_icon_type(self, client: TestClient):
        """Test creating a location with icon type."""
        location_data = {
            "name": "Dragon Lair",
            "latitude": 60.0,
            "longitude": 8.0,
            "icon_type": "cave",
        }

        response = client.post("/api/map-locations", json=location_data)

        assert response.status_code == 201
        data = response.json()
        assert data["icon_type"] == "cave"

    def test_create_location_all_fields(self, client: TestClient):
        """Test creating a location with all fields."""
        location_data = {
            "name": "Capital City",
            "description": "The kingdom's capital",
            "latitude": 62.0,
            "longitude": 9.0,
            "map_id": "main-world",
            "icon_type": "city",
        }

        response = client.post("/api/map-locations", json=location_data)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Capital City"
        assert data["description"] == "The kingdom's capital"
        assert data["map_id"] == "main-world"
        assert data["icon_type"] == "city"

    def test_create_location_missing_name(self, client: TestClient):
        """Test that creating a location without name returns 422."""
        location_data = {
            "latitude": 61.0,
            "longitude": 7.0,
        }

        response = client.post("/api/map-locations", json=location_data)

        assert response.status_code == 422

    def test_create_location_missing_coordinates(self, client: TestClient):
        """Test that creating a location without coordinates returns 422."""
        location_data = {
            "name": "Test Location",
        }

        response = client.post("/api/map-locations", json=location_data)

        assert response.status_code == 422

    def test_list_locations_empty(self, client: TestClient):
        """Test listing locations when none exist."""
        response = client.get("/api/map-locations")

        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_list_locations_multiple(self, client: TestClient):
        """Test listing multiple locations."""
        # Create locations
        locations = [
            {"name": "Village A", "latitude": 61.0, "longitude": 7.0},
            {"name": "Village B", "latitude": 62.0, "longitude": 8.0},
            {"name": "Village C", "latitude": 63.0, "longitude": 9.0},
        ]
        for loc in locations:
            client.post("/api/map-locations", json=loc)

        response = client.get("/api/map-locations")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    def test_get_location_by_id(self, client: TestClient):
        """Test getting a specific location by ID."""
        # Create a location
        create_response = client.post(
            "/api/map-locations",
            json={"name": "Test Village", "latitude": 61.0, "longitude": 7.0}
        )
        location_id = create_response.json()["id"]

        # Get the location
        response = client.get(f"/api/map-locations/{location_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == location_id
        assert data["name"] == "Test Village"

    def test_get_location_not_found(self, client: TestClient):
        """Test getting a non-existent location returns 404."""
        response = client.get("/api/map-locations/nonexistent")

        assert response.status_code == 404

    def test_update_location(self, client: TestClient):
        """Test updating a location."""
        # Create a location
        create_response = client.post(
            "/api/map-locations",
            json={"name": "Original", "latitude": 61.0, "longitude": 7.0}
        )
        location_id = create_response.json()["id"]

        # Update the location
        update_data = {
            "name": "Updated",
            "description": "New description",
            "latitude": 62.0,
            "longitude": 8.0,
        }
        response = client.put(f"/api/map-locations/{location_id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated"
        assert data["description"] == "New description"

    def test_delete_location(self, client: TestClient):
        """Test deleting a location."""
        # Create a location
        create_response = client.post(
            "/api/map-locations",
            json={"name": "To Delete", "latitude": 61.0, "longitude": 7.0}
        )
        location_id = create_response.json()["id"]

        # Delete the location
        response = client.delete(f"/api/map-locations/{location_id}")

        assert response.status_code == 200

        # Verify it's deleted
        get_response = client.get(f"/api/map-locations/{location_id}")
        assert get_response.status_code == 404
