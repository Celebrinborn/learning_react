"""Coordinate label engraving (design doc §9.1).

Creates a temporary FONT object with the canonical q,r,s string, converts
it to a mesh via the direct data API (no bpy.ops), positions it through
the label-anchor transform, and Boolean-differences it into the tile.
The temporary cutter is removed by apply_boolean.
"""

# pyright: reportMissingImports=none, reportMissingModuleSource=none, reportMissingTypeStubs=none, reportUnknownMemberType=none, reportUnknownVariableType=none, reportUnknownArgumentType=none, reportUnknownParameterType=none, reportUntypedBaseClass=none

from __future__ import annotations

import bpy

from .coordinates import CubeCoord
from .mesh_ops import BooleanResult, apply_boolean
from .naming import ROLE_LABEL_ANCHOR, label_string

# Safety margin so the cutter penetrates beyond the target face (§9.1).
_CUT_MARGIN: float = 0.05


def find_label_anchor(
    template: bpy.types.Object,
) -> bpy.types.Object | None:
    """Return the template's label-anchor Empty, or None if absent."""
    for child in template.children:
        if child.get("hg_role") == ROLE_LABEL_ANCHOR:
            return child
    return None


def engrave_label(
    tile: bpy.types.Object,
    anchor: bpy.types.Object,
    coord: CubeCoord,
    size_mm: float,
    depth_mm: float,
) -> BooleanResult:
    """Engrave the canonical q,r,s label into ``tile`` at ``anchor``.

    The cutter is a temporary FONT object converted to a mesh, positioned
    by the anchor's local transform applied through the tile's world
    transform, then Boolean-differenced. Returns a structured result.
    """
    curve: bpy.types.FontCurve = bpy.data.curves.new(name="HG_LABEL", type="FONT")
    curve.body = label_string(coord)
    curve.size = size_mm
    curve.align_x = "CENTER"
    curve.align_y = "CENTER"
    curve.extrude = depth_mm + _CUT_MARGIN

    cutter: bpy.types.Object = bpy.data.objects.new("HG_LABEL_CUTTER", curve)
    bpy.context.scene.collection.objects.link(cutter)
    cutter.matrix_world = tile.matrix_world @ anchor.matrix_local

    # Convert the FONT to a mesh via the direct data API (headless-safe).
    # An object's data type cannot be swapped in place, so the FONT object
    # is replaced by a mesh object carrying the same world transform.
    depsgraph: bpy.types.Depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated: bpy.types.Object = cutter.evaluated_get(depsgraph)
    mesh: bpy.types.Mesh = bpy.data.meshes.new_from_object(evaluated)

    old_curve: bpy.types.FontCurve = cutter.data
    bpy.data.objects.remove(cutter, do_unlink=True)
    bpy.data.curves.remove(old_curve)

    cutter_mesh: bpy.types.Object = bpy.data.objects.new("HG_LABEL_CUTTER", mesh)
    bpy.context.scene.collection.objects.link(cutter_mesh)
    cutter_mesh.matrix_world = tile.matrix_world @ anchor.matrix_local

    return apply_boolean(tile, cutter_mesh, "DIFFERENCE", "EXACT")
