"""Border tests for deterministic naming (design doc §6.5, §10).

Object names use explicit signs (positive/zero -> '+', negative -> '-');
the canonical label string is plain comma-separated integers.
"""

from __future__ import annotations

from hex_heightmap_generator.coordinates import CubeCoord
from hex_heightmap_generator.naming import (
    COLLECTION_GENERATED,
    GROUP_TERRAIN_SURFACE,
    ROLE_GENERATED_TILE,
    ROLE_LABEL_ANCHOR,
    ROLE_TEMPLATE,
    label_string,
    tile_object_name,
)


def test_object_name_positive_negative() -> None:
    assert tile_object_name(CubeCoord(2, -1, -1)) == "HG_q+2_r-1_s-1"


def test_object_name_all_zero() -> None:
    assert tile_object_name(CubeCoord(0, 0, 0)) == "HG_q+0_r+0_s+0"


def test_object_name_mixed() -> None:
    assert tile_object_name(CubeCoord(1, 0, -1)) == "HG_q+1_r+0_s-1"
    assert tile_object_name(CubeCoord(1, -1, 0)) == "HG_q+1_r-1_s+0"


def test_object_name_negative_q() -> None:
    assert tile_object_name(CubeCoord(-1, 1, 0)) == "HG_q-1_r+1_s+0"


def test_object_name_is_deterministic() -> None:
    coord = CubeCoord(3, -2, -1)
    assert tile_object_name(coord) == tile_object_name(coord)


def test_label_string_plain_integers() -> None:
    assert label_string(CubeCoord(2, -1, -1)) == "2,-1,-1"
    assert label_string(CubeCoord(0, 0, 0)) == "0,0,0"
    assert label_string(CubeCoord(1, 0, -1)) == "1,0,-1"


def test_scene_contract_constants() -> None:
    assert GROUP_TERRAIN_SURFACE == "HG_TERRAIN_SURFACE"
    assert COLLECTION_GENERATED == "HG_GENERATED"
    assert ROLE_TEMPLATE == "template"
    assert ROLE_LABEL_ANCHOR == "label_anchor"
    assert ROLE_GENERATED_TILE == "generated_tile"
