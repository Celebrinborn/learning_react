"""Border tests for the engraved coordinate label (design doc §9.1).

Asserts outcomes: engraving changes the tile's underside geometry, the
temporary cutter object is removed from the scene, and the label string
is the canonical q,r,s. Run via the Blender background harness.
"""

# pyright: reportMissingImports=none, reportMissingModuleSource=none, reportMissingTypeStubs=none, reportUnknownMemberType=none, reportUnknownVariableType=none, reportUnknownArgumentType=none, reportUnknownParameterType=none, reportUntypedBaseClass=none

from __future__ import annotations

from pathlib import Path
import tempfile

import bpy

from hex_heightmap_generator.coordinates import CubeCoord, HexOrientation
from hex_heightmap_generator.heightmap import load_heightmap
from hex_heightmap_generator.label import engrave_label, find_label_anchor
from hex_heightmap_generator.mesh_ops import generate_tile
from hex_heightmap_generator.naming import label_string
from hex_heightmap_generator.validation import MappingParams
from tests.integration import fixture_builder as fx


def _mapping() -> MappingParams:
    return MappingParams(
        raster_origin_x=fx.MAPPING_ORIGIN_X,
        raster_origin_y=fx.MAPPING_ORIGIN_Y,
        pixels_per_unit_x=fx.PIXELS_PER_UNIT,
        pixels_per_unit_y=fx.PIXELS_PER_UNIT,
        raster_y_sign=1.0,
        hex_radius=fx.HEX_RADIUS,
        orientation=HexOrientation.POINTY,
    )


def _make_tile() -> tuple[bpy.types.Object, bpy.types.Object]:
    fx.cleanup_scene()
    tmp: Path = Path(tempfile.mkdtemp(prefix="hg_test_"))
    png: Path = tmp / "g.png"
    fx.build_gradient_heightmap(png)
    hm = load_heightmap(str(png))
    template: bpy.types.Object = fx.build_template()
    collection: bpy.types.Collection = bpy.data.collections.new("HG_GENERATED")
    bpy.context.scene.collection.children.link(collection)
    tile = generate_tile(
        template, collection, CubeCoord(1, 0, -1), hm, _mapping(),
        fx.TERRAIN_BASE_Z, fx.ELEVATION_OFFSET_MM, fx.ELEVATION_RANGE_MM,
    )
    return template, tile


def test_find_label_anchor() -> None:
    template, _ = _make_tile()
    anchor = find_label_anchor(template)
    assert anchor is not None, "label anchor not found"
    assert anchor["hg_role"] == "label_anchor"
    assert anchor.parent is template


def test_engrave_label_changes_geometry_and_removes_cutter() -> None:
    template, tile = _make_tile()
    anchor = find_label_anchor(template)
    assert anchor is not None
    before_verts: int = len(tile.data.vertices)
    before_volume: float = _volume(tile)

    result = engrave_label(tile, anchor, CubeCoord(1, 0, -1), 4.0, 0.6)
    assert result.success, f"engrave failed: {result.message}"
    # Engraving cuts geometry: vertex count or volume must change.
    assert len(tile.data.vertices) != before_verts or _volume(tile) != before_volume, (
        "engraving did not change tile geometry"
    )
    # The temporary cutter must be gone.
    cutter_names = [o.name for o in bpy.data.objects if o.type == "FONT"]
    assert cutter_names == [], f"FONT cutter left behind: {cutter_names}"
    # No Boolean modifier left on the tile.
    assert not any(m.type == "BOOLEAN" for m in tile.modifiers)


def test_label_string_is_canonical() -> None:
    assert label_string(CubeCoord(2, -1, -1)) == "2,-1,-1"


def _volume(obj: bpy.types.Object) -> float:
    import bmesh

    bm: bmesh.types.BMesh = bmesh.new()
    bm.from_mesh(obj.data)
    vol: float = bm.calc_volume(signed=False)
    bm.free()
    return vol
