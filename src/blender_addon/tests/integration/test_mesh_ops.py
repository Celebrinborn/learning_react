"""Border tests for mesh deep-copy + terrain deformation (design doc §8).

Asserts outcomes: the template is unchanged, the generated tile owns a
unique mesh datablock, terrain vertices follow the known gradient, and
non-terrain vertices are untouched. Run via the Blender background harness.
"""

# pyright: reportMissingImports=none, reportMissingModuleSource=none, reportMissingTypeStubs=none, reportUnknownMemberType=none, reportUnknownVariableType=none, reportUnknownArgumentType=none, reportUnknownParameterType=none, reportUntypedBaseClass=none

from __future__ import annotations

from pathlib import Path
import tempfile

import bpy

from hex_heightmap_generator.coordinates import CubeCoord, HexOrientation
from hex_heightmap_generator.heightmap import Heightmap, load_heightmap
from hex_heightmap_generator.mesh_ops import generate_tile
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


def _setup() -> tuple[bpy.types.Object, "Heightmap", Path]:
    fx.cleanup_scene()
    tmp: Path = Path(tempfile.mkdtemp(prefix="hg_test_"))
    png: Path = tmp / "g.png"
    fx.build_gradient_heightmap(png)
    hm: Heightmap = load_heightmap(str(png))
    template: bpy.types.Object = fx.build_template()
    return template, hm, tmp


def test_generate_tile_preserves_template_and_unique_datablock() -> None:
    template, hm, _ = _setup()
    before: list[tuple[float, float, float]] = [
        (v.co.x, v.co.y, v.co.z) for v in template.data.vertices
    ]
    collection: bpy.types.Collection = bpy.data.collections.new("HG_GENERATED")
    bpy.context.scene.collection.children.link(collection)

    tile = generate_tile(
        template,
        collection,
        CubeCoord(0, 0, 0),
        hm,
        _mapping(),
        terrain_base_z=fx.TERRAIN_BASE_Z,
        elevation_offset_mm=fx.ELEVATION_OFFSET_MM,
        elevation_range_mm=fx.ELEVATION_RANGE_MM,
    )

    after: list[tuple[float, float, float]] = [
        (v.co.x, v.co.y, v.co.z) for v in template.data.vertices
    ]
    assert before == after, "template vertices were modified"
    assert tile.data is not template.data, "tile shares mesh data with template"
    assert tile.name == "HG_q+0_r+0_s+0"


def test_generate_tile_deforms_terrain_follows_gradient() -> None:
    template, hm, _ = _setup()
    collection: bpy.types.Collection = bpy.data.collections.new("HG_GENERATED")
    bpy.context.scene.collection.children.link(collection)

    tile = generate_tile(
        template,
        collection,
        CubeCoord(0, 0, 0),
        hm,
        _mapping(),
        terrain_base_z=fx.TERRAIN_BASE_Z,
        elevation_offset_mm=fx.ELEVATION_OFFSET_MM,
        elevation_range_mm=fx.ELEVATION_RANGE_MM,
    )

    for v in tile.data.vertices:
        if v.co.z >= -1e-6:  # was a top (terrain) vertex
            u: float = fx.MAPPING_ORIGIN_X + v.co.x * fx.PIXELS_PER_UNIT
            expected_z: float = (
                u / (fx.GRADIENT_WIDTH - 1)
            ) * fx.ELEVATION_RANGE_MM
            assert abs(v.co.z - expected_z) < 0.05, (
                f"terrain vertex {v.index}: z={v.co.z:.4f} expected {expected_z:.4f}"
            )
        else:  # bottom vertex must be untouched
            assert abs(v.co.z - (-fx.PRISM_HEIGHT)) < 1e-6, (
                f"bottom vertex {v.index} moved: z={v.co.z}"
            )


def test_two_tiles_do_not_share_datablock() -> None:
    template, hm, _ = _setup()
    collection: bpy.types.Collection = bpy.data.collections.new("HG_GENERATED")
    bpy.context.scene.collection.children.link(collection)

    t1 = generate_tile(
        template, collection, CubeCoord(0, 0, 0), hm, _mapping(),
        fx.TERRAIN_BASE_Z, fx.ELEVATION_OFFSET_MM, fx.ELEVATION_RANGE_MM,
    )
    t2 = generate_tile(
        template, collection, CubeCoord(1, -1, 0), hm, _mapping(),
        fx.TERRAIN_BASE_Z, fx.ELEVATION_OFFSET_MM, fx.ELEVATION_RANGE_MM,
    )
    assert t1.data is not t2.data, "two tiles share a mesh datablock"
