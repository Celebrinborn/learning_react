"""Unit tests for auth provider building in AppBuilder."""
from builder import AppBuilder
from auth.providers.entra import EntraAuthProvider


class TestBuildAuthProvider:

    def test_returns_entra_provider(self) -> None:
        builder = AppBuilder()
        provider = builder.build_auth_provider()
        assert isinstance(provider, EntraAuthProvider)
