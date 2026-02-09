"""Integration test: main.py wires auth so /me works end-to-end.

In dev/local_fake mode (the default), /me should return 200 without any token.
This tests the actual app from main.py, not a test-constructed FastAPI app.
"""
from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


class TestAuthWiringLocalFake:
    """With default dev config (local_fake), /me returns a user without a token."""

    def test_me_returns_200(self) -> None:
        response = client.get("/me")
        assert response.status_code == 200

    def test_me_returns_subject(self) -> None:
        response = client.get("/me")
        data = response.json()
        assert "subject" in data
        assert isinstance(data["subject"], str)
        assert len(data["subject"]) > 0
