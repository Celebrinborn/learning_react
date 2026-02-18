"""Integration test: dependencies module wires auth correctly.

Verifies that the dependencies package exposes a callable `authenticate`
dependency built from the AppBuilder.
"""
from dependencies import authenticate


class TestAuthWiring:
    """The dependencies module exposes a wired authenticate callable."""

    def test_authenticate_is_callable(self) -> None:
        assert callable(authenticate)
