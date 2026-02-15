"""Integration test: main.py wires auth so get_current_user is overridden.

Verifies that the app startup correctly wires the EntraAuthProvider
dependency into FastAPI's dependency_overrides.
"""
from auth.dependencies import get_current_user
from main import app


class TestAuthWiring:
    """The app wires get_current_user to an EntraAuthProvider dependency."""

    def test_get_current_user_is_overridden(self) -> None:
        assert get_current_user in app.dependency_overrides
