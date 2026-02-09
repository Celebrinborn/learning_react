"""Unit tests for LocalFakeAuthProvider."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from auth.providers.local_fake import LocalFakeAuthProvider
from auth.models import UserPrincipal
from auth.dependencies import get_current_user
from routes.auth import router as auth_router


@pytest.fixture
def client() -> TestClient:
    provider = LocalFakeAuthProvider()
    app = FastAPI()
    app.include_router(auth_router)
    app.dependency_overrides[get_current_user] = provider.dependency()
    return TestClient(app)


class TestLocalFakeAuthProvider:
    """LocalFakeAuthProvider returns a hardcoded user without requiring a token."""

    def test_returns_200_without_auth_header(self, client: TestClient) -> None:
        response = client.get("/me")
        assert response.status_code == 200

    def test_returns_user_principal_with_subject(self, client: TestClient) -> None:
        response = client.get("/me")
        data = response.json()
        assert "subject" in data
        assert isinstance(data["subject"], str)
        assert len(data["subject"]) > 0

    def test_returns_200_with_auth_header_present(self, client: TestClient) -> None:
        """Auth header is ignored -- provider does not validate tokens."""
        response = client.get("/me", headers={"Authorization": "Bearer some-token"})
        assert response.status_code == 200
