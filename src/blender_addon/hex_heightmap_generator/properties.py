"""Scene PropertyGroup holding all add-on settings (design doc §6.6, §11).

The template is an object picker (PointerProperty to Object), which is
valid in a PropertyGroup (unlike an operator property). The generate
operator and the N-panel both read from ``context.scene.hg_settings``.
"""

# pyright: reportMissingImports=none, reportMissingModuleSource=none, reportMissingTypeStubs=none, reportUnknownMemberType=none, reportUnknownVariableType=none, reportUnknownArgumentType=none, reportUnknownParameterType=none, reportUntypedBaseClass=none, reportOptionalMemberAccess=none, reportOptionalSubscript=none, reportInvalidTypeForm=none

from __future__ import annotations

import bpy
from bpy.props import (
    EnumProperty,
    FloatProperty,
    PointerProperty,
    StringProperty,
)
from bpy.types import PropertyGroup


class HexGenSettings(PropertyGroup):
    """All Hex Heightmap Generator settings (design doc §6.6)."""

    template: PointerProperty(
        type=bpy.types.Object,
        name="Template",
        description="Base hex template object",
    )
    heightmap_path: StringProperty(
        name="Heightmap File", subtype="FILE_PATH", default=""
    )
    orientation: EnumProperty(
        name="Hex Orientation",
        items=[("POINTY", "Pointy", "Pointy-top"), ("FLAT", "Flat", "Flat-top")],
        default="POINTY",
    )
    raster_origin_x: FloatProperty(name="Raster Origin X", default=0.0)
    raster_origin_y: FloatProperty(name="Raster Origin Y", default=0.0)
    pixels_per_unit_x: FloatProperty(name="Pixels / Model Unit X", default=1.0)
    pixels_per_unit_y: FloatProperty(name="Pixels / Model Unit Y", default=1.0)
    raster_y_direction: EnumProperty(
        name="Raster Y Direction",
        items=[("DOWN", "Down", ""), ("UP", "Up", "")],
        default="DOWN",
    )
    elevation_range_mm: FloatProperty(name="Elevation Range (mm)", default=10.0)
    elevation_offset_mm: FloatProperty(name="Elevation Offset (mm)", default=0.0)
    label_size_mm: FloatProperty(name="Label Size (mm)", default=4.0)
    label_depth_mm: FloatProperty(name="Label Depth (mm)", default=0.6)
    batch_text: StringProperty(name="Coordinates", default="")


classes: tuple[type[PropertyGroup], ...] = (HexGenSettings,)


def register() -> None:
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.hg_settings = bpy.props.PointerProperty(type=HexGenSettings)


def unregister() -> None:
    del bpy.types.Scene.hg_settings
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
