"""N-panel for the Hex Heightmap Generator (design doc §11).

3D Viewport > Sidebar > Hex Generator. The panel is pure UI glue: it
binds widgets to the scene settings PropertyGroup and invokes the
setup/generate/clear operators. No geometry logic lives here.
"""

# pyright: reportMissingImports=none, reportMissingModuleSource=none, reportMissingTypeStubs=none, reportUnknownMemberType=none, reportUnknownVariableType=none, reportUnknownArgumentType=none, reportUnknownParameterType=none, reportUntypedBaseClass=none, reportOptionalMemberAccess=none, reportOptionalSubscript=none

from __future__ import annotations

import bpy
from bpy.types import Panel


class HexgenPanel(Panel):
    """Hex Generator sidebar panel (design doc §11)."""

    bl_label: str = "Hex Generator"
    bl_idname: str = "VIEW3D_PT_hexgen"
    bl_space_type: str = "VIEW_3D"
    bl_region_type: str = "UI"
    bl_category: str = "Hex Generator"

    def draw(self, context: bpy.types.Context) -> None:
        layout: bpy.types.UILayout = self.layout
        settings = context.scene.hg_settings

        box: bpy.types.UILayout = layout.box()
        box.label(text="Template", icon="MESH_DATA")
        box.prop(settings, "template", text="Template")
        row: bpy.types.UILayout = box.row()
        row.operator("hexgen.set_template_from_active", text="Set From Active")
        row.operator("hexgen.set_terrain_surface", text="Set Terrain Surface")
        row.operator("hexgen.create_label_anchor", text="Create / Move Label Anchor")

        box = layout.box()
        box.label(text="Heightmap", icon="IMAGE_DATA")
        box.prop(settings, "heightmap_path", text="File")
        box.prop(settings, "orientation", text="Orientation")
        box.prop(settings, "raster_origin_x", text="Raster Origin X")
        box.prop(settings, "raster_origin_y", text="Raster Origin Y")
        box.prop(settings, "pixels_per_unit_x", text="Pixels / Unit X")
        box.prop(settings, "pixels_per_unit_y", text="Pixels / Unit Y")
        box.prop(settings, "raster_y_direction", text="Raster Y Direction")
        box.prop(settings, "elevation_range_mm", text="Elevation Range (mm)")
        box.prop(settings, "elevation_offset_mm", text="Elevation Offset (mm)")

        box = layout.box()
        box.label(text="Label", icon="FONT_DATA")
        box.prop(settings, "label_size_mm", text="Size (mm)")
        box.prop(settings, "label_depth_mm", text="Depth (mm)")

        box = layout.box()
        box.label(text="Tiles", icon="MESH_HEXAGON")
        box.prop(settings, "batch_text", text="Coordinates")
        row = box.row()
        row.operator("hexgen.generate_tiles", text="Generate Tiles")
        row.operator("hexgen.clear_generated", text="Clear Generated Tiles")


classes: tuple[type[Panel], ...] = (HexgenPanel,)


def register() -> None:
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
