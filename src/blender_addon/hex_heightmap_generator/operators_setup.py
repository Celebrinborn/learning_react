"""Setup operators: template, terrain surface, label anchor (design doc §6).

These operators are context-dependent (active object, Edit Mode
selection, 3D cursor) and are isolated here per design doc §14.2.
"""

# pyright: reportMissingImports=none, reportMissingModuleSource=none, reportMissingTypeStubs=none, reportUnknownMemberType=none, reportUnknownVariableType=none, reportUnknownArgumentType=none, reportUnknownParameterType=none, reportUntypedBaseClass=none, reportOptionalMemberAccess=none, reportOptionalSubscript=none

from __future__ import annotations

import bpy
from bpy.types import Operator as OperatorType

from hex_heightmap_generator.naming import (
    GROUP_TERRAIN_SURFACE,
    ROLE_LABEL_ANCHOR,
    ROLE_TEMPLATE,
)


class HexgenSetTemplateFromActive(OperatorType):
    """Mark the active object as the template (must be a MESH)."""

    bl_idname: str = "hexgen.set_template_from_active"
    bl_label: str = "Set From Active Object"
    bl_description: str = "Marks the active object as the base hex template"
    bl_options: set[str] = {"UNDO"}

    def execute(self, context: bpy.types.Context) -> set[str]:
        active: bpy.types.Object | None = context.active_object
        if active is None or active.type != "MESH":
            self.report({"ERROR"}, "Active object is not a mesh")
            return {"CANCELLED"}
        active["hg_role"] = ROLE_TEMPLATE
        return {"FINISHED"}


class HexgenSetTerrainSurface(OperatorType):
    """Store the selected faces' vertices in HG_TERRAIN_SURFACE.

    Reads the Edit Mode face selection, collects every vertex belonging
    to a selected face, and REPLACES the group contents (design doc §6.2).
    """

    bl_idname: str = "hexgen.set_terrain_surface"
    bl_label: str = "Set Terrain Surface"
    bl_description: str = "Stores selected faces' vertices as the terrain surface"
    bl_options: set[str] = {"UNDO"}

    def execute(self, context: bpy.types.Context) -> set[str]:
        active: bpy.types.Object | None = context.active_object
        if active is None or active.type != "MESH":
            self.report({"ERROR"}, "Active object is not a mesh")
            return {"CANCELLED"}

        # Collect vertices belonging to any selected face. poly.select is
        # only meaningful in edit mode, so this is read before any mode
        # change (the user invokes this from edit mode, design doc §4).
        selected_vertex_indices: set[int] = set()
        for poly in active.data.polygons:
            if poly.select:
                selected_vertex_indices.update(poly.vertices)
        if not selected_vertex_indices:
            self.report({"ERROR"}, "No faces selected")
            return {"CANCELLED"}

        # Vertex-group membership can only be modified in object mode, so
        # switch out of edit mode, apply the change, then restore the mode.
        was_edit: bool = context.object.mode == "EDIT"
        if was_edit:
            bpy.ops.object.mode_set(mode="OBJECT")

        # Replace (not append) the group contents.
        group: bpy.types.VertexGroup | None = active.vertex_groups.get(
            GROUP_TERRAIN_SURFACE
        )
        if group is None:
            group = active.vertex_groups.new(name=GROUP_TERRAIN_SURFACE)
        else:
            group.remove(list(range(len(active.data.vertices))))
        group.add(sorted(selected_vertex_indices), 1.0, "REPLACE")

        # Store a setup checksum so Validate can warn on topology changes.
        active["hg_terrain_vertex_count"] = len(selected_vertex_indices)

        if was_edit:
            bpy.ops.object.mode_set(mode="EDIT")
        return {"FINISHED"}


class HexgenCreateLabelAnchor(OperatorType):
    """Create (or move) the label-anchor Empty at the 3D cursor.

    The anchor is parented to the active template object; its local
    transform defines the label position/orientation (design doc §6.3).
    """

    bl_idname: str = "hexgen.create_label_anchor"
    bl_label: str = "Create / Move Label Anchor"
    bl_description: str = "Creates a label-anchor Empty at the 3D cursor"
    bl_options: set[str] = {"UNDO"}

    def execute(self, context: bpy.types.Context) -> set[str]:
        active: bpy.types.Object | None = context.active_object
        if active is None or active.type != "MESH":
            self.report({"ERROR"}, "Active object is not a mesh")
            return {"CANCELLED"}

        cursor: bpy.types.Vector = context.scene.cursor.location
        # Existing anchor? Move it. Otherwise create it.
        anchor: bpy.types.Object | None = None
        for child in active.children:
            if child.get("hg_role") == ROLE_LABEL_ANCHOR:
                anchor = child
                break
        if anchor is None:
            anchor = bpy.data.objects.new("HG_LABEL_ANCHOR", None)
            anchor.empty_display_type = "PLAIN_AXES"
            context.scene.collection.objects.link(anchor)
            anchor.parent = active
            anchor["hg_role"] = ROLE_LABEL_ANCHOR
        # Set the local location from the world cursor position.
        anchor.matrix_parent_inverse = active.matrix_world.inverted()
        anchor.location = active.matrix_world.inverted() @ cursor
        return {"FINISHED"}


classes: tuple[type[OperatorType], ...] = (
    HexgenSetTemplateFromActive,
    HexgenSetTerrainSurface,
    HexgenCreateLabelAnchor,
)


def register() -> None:
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
