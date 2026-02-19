"""Unit tests for BlobAuthorizationProvider."""
import json
from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError

from interfaces.auth.auth import AuthorizationError
from models import UserRole
from models.auth.user_principal import Principal
from providers.auth.authorization_provider import (
    BlobAuthorizationProvider,
    UserDatabase,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

KNOWN_OID = "25edd424-4428-4952-80e1-9e0a3fe718a6"
UNKNOWN_OID = "00000000-0000-0000-0000-000000000000"

USERS_JSON: bytes = json.dumps(
    {
        KNOWN_OID: {
            "roles": ["dm", "player"],
            "name": "Cameron",
            "preferred_username": "cameronjunkmail1@gmail.com",
            "subject": KNOWN_OID,
        }
    }
).encode()


def _make_principal(oid: str = KNOWN_OID) -> Principal:
    return Principal(
        subject=oid,
        entra_object_id=oid,
        issuer="https://test.ciamlogin.com/test/v2.0",
        audience="api://test",
        expiration=9999999999,
        issued_at=0,
        not_before=0,
        name=None,
        prefered_username=None,
    )


def _make_blob(data: bytes = USERS_JSON) -> AsyncMock:
    """Return a mock IBlob whose read() returns the given bytes."""
    blob = AsyncMock()
    blob.read = AsyncMock(return_value=data)
    return blob


# ---------------------------------------------------------------------------
# UserDatabase.from_json
# ---------------------------------------------------------------------------


class TestUserDatabaseFromJson:
    def test_parses_valid_json(self) -> None:
        db = UserDatabase.from_json(USERS_JSON)
        assert KNOWN_OID in db.users
        record = db.users[KNOWN_OID]
        assert record.name == "Cameron"
        assert record.preferred_username == "cameronjunkmail1@gmail.com"
        assert UserRole.DM in record.roles
        assert UserRole.PLAYER in record.roles

    def test_invalid_role_raises_validation_error(self) -> None:
        bad = json.dumps(
            {
                KNOWN_OID: {
                    "roles": ["not_a_real_role"],
                    "name": "X",
                    "preferred_username": "x@x.com",
                    "subject": KNOWN_OID,
                }
            }
        ).encode()
        with pytest.raises(ValidationError):
            UserDatabase.from_json(bad)

    def test_empty_users_file(self) -> None:
        db = UserDatabase.from_json(b"{}")
        assert db.users == {}


# ---------------------------------------------------------------------------
# BlobAuthorizationProvider.get_roles
# ---------------------------------------------------------------------------


class TestBlobAuthorizationProviderGetRoles:
    @pytest.mark.asyncio
    async def test_known_user_gets_correct_roles(self) -> None:
        provider = BlobAuthorizationProvider(_make_blob())
        principal = _make_principal(KNOWN_OID)

        roles = await provider.get_roles(principal)

        assert UserRole.DM in roles
        assert UserRole.PLAYER in roles

    @pytest.mark.asyncio
    async def test_unknown_user_gets_empty_roles(self) -> None:
        provider = BlobAuthorizationProvider(_make_blob())
        principal = _make_principal(UNKNOWN_OID)

        roles = await provider.get_roles(principal)

        assert roles == []

    @pytest.mark.asyncio
    async def test_blob_read_is_cached(self) -> None:
        blob = _make_blob()
        provider = BlobAuthorizationProvider(blob)
        principal = _make_principal(KNOWN_OID)

        await provider.get_roles(principal)
        await provider.get_roles(principal)

        blob.read.assert_awaited_once()


# ---------------------------------------------------------------------------
# BlobAuthorizationProvider.required_cnf_roles
# ---------------------------------------------------------------------------


class TestBlobAuthorizationProviderRequiredCnfRoles:
    @pytest.mark.asyncio
    async def test_user_with_required_role_passes(self) -> None:
        provider = BlobAuthorizationProvider(_make_blob())
        principal = _make_principal(KNOWN_OID)

        result = await provider.required_cnf_roles(
            principal, [[UserRole.DM]]
        )

        assert result is principal

    @pytest.mark.asyncio
    async def test_user_satisfies_one_of_in_set(self) -> None:
        """User with PLAYER satisfies [ADMIN | PLAYER]."""
        provider = BlobAuthorizationProvider(_make_blob())
        principal = _make_principal(KNOWN_OID)

        result = await provider.required_cnf_roles(
            principal, [[UserRole.ADMIN, UserRole.PLAYER]]
        )

        assert result is principal

    @pytest.mark.asyncio
    async def test_user_satisfies_all_cnf_sets(self) -> None:
        """User with DM + PLAYER satisfies [DM] AND [PLAYER]."""
        provider = BlobAuthorizationProvider(_make_blob())
        principal = _make_principal(KNOWN_OID)

        result = await provider.required_cnf_roles(
            principal, [[UserRole.DM], [UserRole.PLAYER]]
        )

        assert result is principal

    @pytest.mark.asyncio
    async def test_user_missing_one_cnf_set_raises(self) -> None:
        """User with DM + PLAYER fails [DM] AND [ADMIN]."""
        provider = BlobAuthorizationProvider(_make_blob())
        principal = _make_principal(KNOWN_OID)

        with pytest.raises(AuthorizationError):
            await provider.required_cnf_roles(
                principal, [[UserRole.DM], [UserRole.ADMIN]]
            )

    @pytest.mark.asyncio
    async def test_unknown_user_raises_authorization_error(self) -> None:
        provider = BlobAuthorizationProvider(_make_blob())
        principal = _make_principal(UNKNOWN_OID)

        with pytest.raises(AuthorizationError):
            await provider.required_cnf_roles(
                principal, [[UserRole.PLAYER]]
            )

    @pytest.mark.asyncio
    async def test_empty_required_roles_always_passes(self) -> None:
        """No role requirements — even unknown users pass."""
        provider = BlobAuthorizationProvider(_make_blob())
        principal = _make_principal(UNKNOWN_OID)

        result = await provider.required_cnf_roles(principal, [])

        assert result is principal
