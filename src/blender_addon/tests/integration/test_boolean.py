"""Border tests for the generic Boolean helper (design doc §9.2).

Asserts outcomes: DIFFERENCE removes the operand's volume from the target,
UNION adds it, the result is a valid non-empty mesh, and no temporary
modifier/operand is left behind. Run via the Blender background harness.
"""

# pyright: reportMissingImports=none, reportMissingModuleSource=none, reportMissingTypeStubs=none, reportUnknownMemberType=none, reportUnknownVariableType=none, reportUnknownArgumentType=none, reportUnknownParameterType=none, reportUntypedBaseClass=none

from __future__ import annotations

import bmesh
import bpy

from hex_heightmap_generator.mesh_ops import apply_boolean
from tests.integration import fixture_builder as fx


def _make_cube(name: str, size: float, z: float) -> bpy.types.Object:
    bm: bmesh.types.BMesh = bmesh.new()
    bmesh.ops.create_cube(bm, size=size)
    for vert in bm.verts:
        vert.co.z += z
    mesh: bpy.types.Mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj: bpy.types.Object = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def _volume(obj: bpy.types.Object) -> float:
    bm: bmesh.types.BMesh = bmesh.new()
    bm.from_mesh(obj.data)
    vol: float = bm.calc_volume(signed=False)
    bm.free()
    return vol


def test_boolean_difference_reduces_volume() -> None:
    fx.cleanup_scene()
    target = _make_cube("target", 2.0, 0.0)
    operand = _make_cube("operand", 1.0, 0.0)  # fully inside target
    operand_name: str = operand.name
    base_volume: float = _volume(target)

    result = apply_boolean(target, operand, "DIFFERENCE", "EXACT")
    assert result.success, f"Boolean failed: {result.message}"
    assert _volume(target) < base_volume, "DIFFERENCE did not reduce volume"
    # Operand must be cleaned up.
    assert operand_name not in [o.name for o in bpy.data.objects]
    # No Boolean modifier left on the target.
    assert not any(m.type == "BOOLEAN" for m in target.modifiers)


def test_boolean_union_increases_volume() -> None:
    fx.cleanup_scene()
    target = _make_cube("target", 1.0, 0.0)
    operand = _make_cube("operand", 1.0, 1.5)  # overlapping, extends target
    operand_name: str = operand.name
    base_volume: float = _volume(target)

    result = apply_boolean(target, operand, "UNION", "EXACT")
    assert result.success, f"Boolean failed: {result.message}"
    assert _volume(target) > base_volume, "UNION did not increase volume"
    assert operand_name not in [o.name for o in bpy.data.objects]
    assert not any(m.type == "BOOLEAN" for m in target.modifiers)


def test_boolean_result_is_valid_mesh() -> None:
    fx.cleanup_scene()
    target = _make_cube("target", 2.0, 0.0)
    operand = _make_cube("operand", 1.0, 0.0)
    result = apply_boolean(target, operand, "DIFFERENCE", "EXACT")
    assert result.success
    assert target.type == "MESH"
    assert len(target.data.vertices) > 0, "Boolean produced an empty mesh"
