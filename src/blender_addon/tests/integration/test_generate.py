"""Border tests for batch generation + clear (design doc §10, §17, §19.2).

Asserts outcomes: 10 valid coords -> 10 distinct engraved tiles with
custom props and the template intact; a malformed line blocks preflight
(zero geometry); a name collision skips only that tile (no overwrite)
while earlier tiles remain intact. Run via the Blender background harness.
"""

# pyright: reportMissingImports=none, reportMissingModuleSource=none, reportMissingTypeStubs=none, reportUnknownMemberType=none, reportUnknownVariableType=none, reportUnknownArgumentType=none, reportUnknownParameterType=none, reportUntypedBaseClass=none, reportOptionalMemberAccess=none, reportOptionalSubscript=none

from __future__ import annotations

from pathlib import Path
import tempfile
from typing import Callable

import bpy

from hex_heightmap_generator.coordinates import CubeCoord
from hex_heightmap_generator.naming import (
    COLLECTION_GENERATED,
    ROLE_GENERATED_TILE,
    tile_object_name,
)
from tests.integration import fixture_builder as fx

TEN_COORDS: str = "\n".join(
    [
        "0,0,0",
        "1,0,-1",
        "1,-1,0",
        "0,1,-1",
        "-1,0,1",
        "-1,1,0",
        "2,0,-2",
        "2,-1,-1",
        "0,-1,1",
        "-2,0,2",
    ]
)


def _configure(template: bpy.types.Object, png: str, batch_text: str) -> None:
    """Populate the scene settings the generate operator reads."""
    s = bpy.context.scene.hg_settings
    s.template = template
    s.heightmap_path = png
    s.orientation = "POINTY"
    s.raster_origin_x = fx.MAPPING_ORIGIN_X
    s.raster_origin_y = fx.MAPPING_ORIGIN_Y
    s.pixels_per_unit_x = fx.PIXELS_PER_UNIT
    s.pixels_per_unit_y = fx.PIXELS_PER_UNIT
    s.raster_y_direction = "DOWN"
    s.elevation_range_mm = fx.ELEVATION_RANGE_MM
    s.elevation_offset_mm = fx.ELEVATION_OFFSET_MM
    s.label_size_mm = 4.0
    s.label_depth_mm = 0.6
    s.batch_text = batch_text


def _setup_scene() -> tuple[bpy.types.Object, str]:
    fx.cleanup_scene()
    tmp: Path = Path(tempfile.mkdtemp(prefix="hg_test_"))
    png: Path = tmp / "g.png"
    fx.build_gradient_heightmap(png)
    template: bpy.types.Object = fx.build_template()
    return template, str(png)


def _generated_tiles() -> list[bpy.types.Object]:
    collection: bpy.types.Collection | None = bpy.data.collections.get(
        COLLECTION_GENERATED
    )
    if collection is None:
        return []
    return [o for o in collection.objects if o.get("hg_role") == ROLE_GENERATED_TILE]


def _invoke(op: Callable[[], set[str]]) -> tuple[bool, set[str]]:
    """Invoke an operator; return (raised, result).

    In background mode an operator's ERROR report raises a RuntimeError
    instead of returning CANCELLED, so a raise is treated as a blocked
    (rejected) invocation.
    """
    try:
        result: set[str] = op()
        return False, result
    except RuntimeError:
        return True, set()


def test_generate_ten_tiles_template_intact() -> None:
    template, png = _setup_scene()
    before: list[tuple[float, float, float]] = [
        (v.co.x, v.co.y, v.co.z) for v in template.data.vertices
    ]
    _configure(template, png, TEN_COORDS)
    result = bpy.ops.hexgen.generate_tiles()
    assert "CANCELLED" not in result

    tiles: list[bpy.types.Object] = _generated_tiles()
    assert len(tiles) == 10, f"expected 10 tiles, got {len(tiles)}"

    # Template unchanged.
    after: list[tuple[float, float, float]] = [
        (v.co.x, v.co.y, v.co.z) for v in template.data.vertices
    ]
    assert before == after, "template was modified"

    # Each tile has custom props and a unique datablock.
    datablocks: set[int] = set()
    for tile in tiles:
        assert tile["hg_q"] in (-2, -1, 0, 1, 2), f"tile {tile.name} has bad hg_q"
        assert "hg_r" in tile and "hg_s" in tile
        assert "hg_source_template" in tile
        datablocks.add(id(tile.data))
    assert len(datablocks) == 10, "tiles share mesh datablocks"


def _generate() -> set[str]:
    return bpy.ops.hexgen.generate_tiles()


def test_generate_malformed_line_blocks_preflight() -> None:
    template, png = _setup_scene()
    _configure(template, png, "0,0,0\n1,1,1")  # second line has nonzero sum
    raised, result = _invoke(_generate)
    assert raised or "CANCELLED" in result, "malformed line must block"
    assert _generated_tiles() == [], "malformed line must block all geometry"


def test_generate_name_collision_skips_that_tile_only() -> None:
    template, png = _setup_scene()
    # Pre-create a tile that collides with the first batch coordinate.
    # Get-or-create (the collection may already exist from an earlier test
    # in the same Blender session; .new() would silently rename it).
    collection: bpy.types.Collection | None = bpy.data.collections.get(
        COLLECTION_GENERATED
    )
    if collection is None:
        collection = bpy.data.collections.new(COLLECTION_GENERATED)
        bpy.context.scene.collection.children.link(collection)
    existing: bpy.types.Object = bpy.data.objects.new(
        tile_object_name(CubeCoord(0, 0, 0)), None
    )
    collection.objects.link(existing)

    _configure(template, png, TEN_COORDS)
    result = bpy.ops.hexgen.generate_tiles()
    assert "CANCELLED" not in result

    tiles: list[bpy.types.Object] = _generated_tiles()
    # The colliding (0,0,0) tile is the pre-existing Empty (not a mesh tile);
    # the other 9 coordinates produced mesh tiles.
    mesh_tiles: list[bpy.types.Object] = [t for t in tiles if t.type == "MESH"]
    assert len(mesh_tiles) == 9, f"expected 9 mesh tiles, got {len(mesh_tiles)}"
    # The pre-existing object was not overwritten (still an Empty).
    assert existing.type == "EMPTY", "existing object was overwritten"


def test_clear_generated_removes_only_generated_tiles() -> None:
    template, png = _setup_scene()
    _configure(template, png, TEN_COORDS)
    bpy.ops.hexgen.generate_tiles()
    assert len(_generated_tiles()) == 10

    # A user object inside HG_GENERATED that is NOT a generated tile.
    collection: bpy.types.Collection = bpy.data.collections.get(COLLECTION_GENERATED)
    assert collection is not None
    user_obj: bpy.types.Object = bpy.data.objects.new("user_object", None)
    collection.objects.link(user_obj)

    result = bpy.ops.hexgen.clear_generated()
    assert "CANCELLED" not in result
    assert _generated_tiles() == [], "generated tiles were not cleared"
    # The user object must survive.
    assert user_obj.name in [o.name for o in bpy.data.objects]
