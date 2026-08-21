"""Border tests for the setup operators (design doc §6.2, §6.3).

Asserts outcomes: template role is set (and non-mesh rejected), the
terrain-surface group is replaced from a face selection (and empty
selection rejected), and the label anchor is created at the cursor and
parented. Run via the Blender background harness.
"""

# pyright: reportMissingImports=none, reportMissingModuleSource=none, reportMissingTypeStubs=none, reportUnknownMemberType=none, reportUnknownVariableType=none, reportUnknownArgumentType=none, reportUnknownParameterType=none, reportUntypedBaseClass=none

from __future__ import annotations

from typing import Callable

import bpy

from hex_heightmap_generator.naming import (
    GROUP_TERRAIN_SURFACE,
    ROLE_LABEL_ANCHOR,
    ROLE_TEMPLATE,
)
from tests.integration import fixture_builder as fx


def _make_mesh(name: str) -> bpy.types.Object:
    import bmesh

    bm: bmesh.types.BMesh = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    mesh: bpy.types.Mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj: bpy.types.Object = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def _make_empty(name: str) -> bpy.types.Object:
    obj: bpy.types.Object = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def _activate(obj: bpy.types.Object) -> None:
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def _invoke(op: Callable[[], set[str]]) -> bool:
    """Invoke an operator; return True if it was rejected.

    In background mode an operator's error report raises a RuntimeError
    instead of returning CANCELLED, so both are treated as rejection.
    """
    try:
        result: set[str] = op()
    except RuntimeError:
        return True
    return "CANCELLED" in result


def test_set_template_from_active_sets_role() -> None:
    fx.cleanup_scene()
    mesh: bpy.types.Object = _make_mesh("hex")
    _activate(mesh)
    rejected: bool = _invoke(bpy.ops.hexgen.set_template_from_active)
    assert not rejected
    assert mesh["hg_role"] == ROLE_TEMPLATE


def test_set_template_from_active_rejects_non_mesh() -> None:
    fx.cleanup_scene()
    empty: bpy.types.Object = _make_empty("not_a_mesh")
    _activate(empty)
    rejected: bool = _invoke(bpy.ops.hexgen.set_template_from_active)
    assert rejected
    assert empty.get("hg_role") != ROLE_TEMPLATE


def test_set_terrain_surface_replaces_group_from_faces() -> None:
    fx.cleanup_scene()
    template: bpy.types.Object = fx.build_template()
    _activate(template)
    # Enter edit mode and select only the top faces. The operator reads
    # poly.select, which is only meaningful in edit mode, so it is
    # invoked while still in edit mode (the real user workflow).
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="DESELECT")
    bpy.ops.mesh.select_mode(type="FACE")
    for poly in template.data.polygons:
        if poly.center.z > -1e-6:  # top face
            poly.select = True
    rejected: bool = _invoke(bpy.ops.hexgen.set_terrain_surface)
    bpy.ops.object.mode_set(mode="OBJECT")
    assert not rejected
    group: bpy.types.VertexGroup | None = template.vertex_groups.get(
        GROUP_TERRAIN_SURFACE
    )
    assert group is not None
    # Every top vertex is in the group; no bottom vertex is.
    for vert in template.data.vertices:
        in_group: bool = any(
            g.group == group.index and g.weight > 0.0 for g in vert.groups
        )
        if vert.co.z > -1e-6:
            assert in_group, f"top vertex {vert.index} missing from group"
        else:
            assert not in_group, f"bottom vertex {vert.index} in group"


def test_set_terrain_surface_rejects_empty_selection() -> None:
    fx.cleanup_scene()
    template: bpy.types.Object = fx.build_template()
    _activate(template)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="DESELECT")
    rejected: bool = _invoke(bpy.ops.hexgen.set_terrain_surface)
    bpy.ops.object.mode_set(mode="OBJECT")
    assert rejected
    # A rejected call must not have cleared the existing group contents.
    group: bpy.types.VertexGroup | None = template.vertex_groups.get(
        GROUP_TERRAIN_SURFACE
    )
    assert group is not None
    member_count: int = sum(
        1
        for vert in template.data.vertices
        if any(g.group == group.index and g.weight > 0.0 for g in vert.groups)
    )
    assert member_count > 0, "rejected call cleared the terrain group"


def test_create_label_anchor_at_cursor_parented() -> None:
    fx.cleanup_scene()
    template: bpy.types.Object = fx.build_template()
    _activate(template)
    bpy.context.scene.cursor.location = (0.5, -0.5, -2.0)
    result = bpy.ops.hexgen.create_label_anchor()
    assert "CANCELLED" not in result
    anchor: bpy.types.Object | None = None
    for child in template.children:
        if child.get("hg_role") == ROLE_LABEL_ANCHOR:
            anchor = child
    assert anchor is not None, "label anchor not created"
    assert anchor.parent is template
    assert abs(anchor.location.z - (-2.0)) < 1e-4
