"""Integration tests for auth API endpoints.

Tests the /me endpoint at the HTTP boundary:
- No token -> 401
- Invalid token -> 401
- Expired token -> 401
- Valid token -> 200 with user info
- Existing unprotected routes still work
"""
from datetime import datetime, timedelta, timezone
import uuid

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import FastAPI
from fastapi.testclient import TestClient
import jwt
import pytest

from dependencies import authenticate
from dependencies.authentication import build_authentication_dependency
from providers.auth.authentication_provider import EntraAuthProvider
from routes.auth import router as auth_router

TEST_ISSUER = "https://test.ciamlogin.com/test-tenant/v2.0"
TEST_AUDIENCE = "api://test-api"
TEST_SUBJECT = "test-user-id-123"
TEST_OID = "00000000-0000-0000-0000-000000000001"


@pytest.fixture(scope="module")
def test_keys():
    """Generate RSA key pair for test JWT signing."""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return private_pem, public_pem


def make_token(private_pem: bytes, **claims_override: str | int) -> str:
    """Create a signed JWT with the given claims."""
    now = datetime.now(timezone.utc)
    claims: dict[str, str | int] = {
        "oid": TEST_OID,
        "sub": TEST_SUBJECT,
        "iss": TEST_ISSUER,
        "aud": TEST_AUDIENCE,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=1)).timestamp()),
        "nbf": int(now.timestamp()),
        "jti": str(uuid.uuid4()),
        "scp": "access_as_user",
    }
    claims.update(claims_override)
    return jwt.encode(claims, private_pem, algorithm="RS256")


@pytest.fixture
def auth_provider(test_keys):
    """Create an EntraAuthProvider configured with test keys."""
    _, public_pem = test_keys
    provider = EntraAuthProvider(
        issuer=TEST_ISSUER,
        audience=TEST_AUDIENCE,
        jwks_url="https://test.example.com/keys",
    )
    provider._load_pem(public_pem)
    return provider


@pytest.fixture
def app(auth_provider):
    """Create a FastAPI app with auth routes using the test auth provider."""
    app = FastAPI()
    app.include_router(auth_router)
    app.dependency_overrides[authenticate] = build_authentication_dependency(
        authenticator=auth_provider
    )
    return app


@pytest.fixture
def client(app: FastAPI):
    """Create a test client."""
    return TestClient(app)


class TestMeEndpoint:
    """Tests for GET /me - returns current authenticated user."""

    def test_returns_401_when_no_token(self, client: TestClient):
        """Unauthenticated requests are rejected."""
        response = client.get("/me")
        assert response.status_code == 401

    def test_returns_401_when_no_bearer_prefix(self, client: TestClient):
        """Token without Bearer prefix is rejected."""
        response = client.get("/me", headers={"Authorization": "some-token"})
        assert response.status_code == 401

    def test_returns_401_when_invalid_token(self, client: TestClient):
        """Garbage token is rejected."""
        response = client.get("/me", headers={"Authorization": "Bearer not-a-jwt"})
        assert response.status_code == 401

    def test_returns_401_when_expired_token(self, client: TestClient, test_keys):
        """Expired tokens are rejected."""
        private_pem, _ = test_keys
        expired = make_token(
            private_pem,
            iat=int((datetime.now(timezone.utc) - timedelta(hours=2)).timestamp()),
            exp=int((datetime.now(timezone.utc) - timedelta(hours=1)).timestamp()),
        )
        response = client.get("/me", headers={"Authorization": f"Bearer {expired}"})
        assert response.status_code == 401

    def test_returns_401_when_wrong_audience(self, client: TestClient, test_keys):
        """Tokens for a different audience are rejected."""
        private_pem, _ = test_keys
        wrong_aud = make_token(private_pem, aud="api://wrong-api")
        response = client.get("/me", headers={"Authorization": f"Bearer {wrong_aud}"})
        assert response.status_code == 401

    def test_returns_401_when_wrong_issuer(self, client: TestClient, test_keys):
        """Tokens from a different issuer are rejected."""
        private_pem, _ = test_keys
        wrong_iss = make_token(private_pem, iss="https://evil.example.com/v2.0")
        response = client.get("/me", headers={"Authorization": f"Bearer {wrong_iss}"})
        assert response.status_code == 401

    def test_returns_200_with_user_info_when_valid_token(
        self, client: TestClient, test_keys
    ):
        """Valid token returns user info including subject."""
        private_pem, _ = test_keys
        token = make_token(private_pem)
        response = client.get("/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        data = response.json()
        assert data["entra_object_id"] == TEST_OID


class TestExistingRoutes:
    """Ensure existing routes remain unaffected by auth changes."""

    def test_health_endpoint_still_works(self):
        """Health check doesn't require auth."""
        from main import app

        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200

    def test_root_endpoint_still_works(self):
        """Root endpoint doesn't require auth."""
        from main import app

        client = TestClient(app)
        response = client.get("/")
        assert response.status_code == 200
