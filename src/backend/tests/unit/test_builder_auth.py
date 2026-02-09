"""Unit tests for auth provider building in AppBuilder."""
import copy

import pytest

from config import CONFIGS
from builder import AppBuilder
from auth.providers.local_fake import LocalFakeAuthProvider
from auth.providers.entra import EntraAuthProvider


def _make_config(auth_mode: str) -> dict:
    """Create a test config with the given auth mode."""
    config = copy.deepcopy(CONFIGS["dev"])
    config["auth"]["auth_mode"] = auth_mode
    return config


class TestBuildAuthProvider:

    def test_local_fake_returns_local_fake_provider(self) -> None:
        builder = AppBuilder(_make_config("local_fake"))
        provider = builder.build_auth_provider()
        assert isinstance(provider, LocalFakeAuthProvider)

    def test_entra_returns_entra_provider(self) -> None:
        builder = AppBuilder(_make_config("entra_external_id"))
        provider = builder.build_auth_provider()
        assert isinstance(provider, EntraAuthProvider)

    def test_unknown_mode_raises_value_error(self) -> None:
        builder = AppBuilder(_make_config("unknown_mode"))
        with pytest.raises(ValueError, match="Unsupported auth mode"):
            builder.build_auth_provider()
