"""Deterministic integration-test fixture builder (design doc §19.2).

Builds, in a live Blender scene:
- A hexagonal-prism template with a tessellated (concentric-hexagon) top
  face, a flat bottom, an HG_TERRAIN_SURFACE vertex group on the top
  vertices, and a label-anchor Empty on the underside.
- A synthetic linear-in-x grayscale gradient heightmap PNG.

This is test infrastructure (not feature code); it is exercised by every
integration test. All geometry is deterministic so tests can assert exact
outcomes.
"""

# pyright: reportMissingImports=none, reportMissingModuleSource=none, reportMissingTypeStubs=none, reportUnknownMemberType=none, reportUnknownVariableType=none, reportUnknownArgumentType=none, reportUnknownParameterType=none, reportUntypedBaseClass=none

from __future__ import annotations

import math
from pathlib import Path

import bmesh
import bpy

from hex_heightmap_generator.naming import (
    GROUP_TERRAIN_SURFACE,
    ROLE_LABEL_ANCHOR,
    ROLE_TEMPLATE,
)

# Fixture geometry constants (model units).
HEX_RADIUS: float = 1.0
PRISM_HEIGHT: float = 2.0

# Gradient heightmap constants. Large enough to contain the hex footprints
# of the test coordinates (origin is at the raster center).
GRADIENT_WIDTH: int = 200
GRADIENT_HEIGHT: int = 200

# Mapping parameters the tests use (plane (0,0) -> raster center).
MAPPING_ORIGIN_X: float = GRADIENT_WIDTH / 2.0
MAPPING_ORIGIN_Y: float = GRADIENT_HEIGHT / 2.0
PIXELS_PER_UNIT: float = 20.0
ELEVATION_OFFSET_MM: float = 0.0
ELEVATION_RANGE_MM: float = 10.0
TERRAIN_BASE_Z: float = 0.0


def _hex_angles() -> list[float]:
    """Pointy-top hexagon corner angles (radians): 90 + 60*k."""
    return [math.radians(90.0 + 60.0 * k) for k in range(6)]


def build_template(name: str = "HG_TEMPLATE") -> bpy.types.Object:
    """Create the hexagonal-prism template and return it.

    The top face is tessellated with a concentric-hexagon grid (13
    vertices) and is the terrain surface. The bottom is a flat fan. A
    label-anchor Empty is parented at the underside center.
    """
    bm: bmesh.types.BMesh = bmesh.new()
    angles: list[float] = _hex_angles()
    r: float = HEX_RADIUS
    h: float = PRISM_HEIGHT

    top_outer: list[bmesh.types.BMVert] = []
    top_inner: list[bmesh.types.BMVert] = []
    bottom_outer: list[bmesh.types.BMVert] = []
    for ang in angles:
        cx: float = r * math.cos(ang)
        cy: float = r * math.sin(ang)
        top_outer.append(bm.verts.new((cx, cy, 0.0)))
        top_inner.append(bm.verts.new((cx / 2.0, cy / 2.0, 0.0)))
        bottom_outer.append(bm.verts.new((cx, cy, -h)))
    top_center: bmesh.types.BMVert = bm.verts.new((0.0, 0.0, 0.0))
    bottom_center: bmesh.types.BMVert = bm.verts.new((0.0, 0.0, -h))

    # Top: center fan + ring quads.
    for k in range(6):
        k1: int = (k + 1) % 6
        bm.faces.new((top_center, top_inner[k], top_inner[k1]))
        bm.faces.new(
            (top_inner[k], top_inner[k1], top_outer[k1], top_outer[k])
        )
    # Bottom: fan.
    for k in range(6):
        k1: int = (k + 1) % 6
        bm.faces.new((bottom_center, bottom_outer[k1], bottom_outer[k]))
    # Sides: quads.
    for k in range(6):
        k1: int = (k + 1) % 6
        bm.faces.new(
            (top_outer[k], top_outer[k1], bottom_outer[k1], bottom_outer[k])
        )

    bm.normal_update()
    mesh: bpy.types.Mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()

    obj: bpy.types.Object = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)

    # Terrain surface = all top-face vertices.
    group: bpy.types.VertexGroup = obj.vertex_groups.new(name=GROUP_TERRAIN_SURFACE)
    terrain_indices: list[int] = []
    for vert in mesh.vertices:
        if vert.co.z > -1e-6:  # top face at z == 0
            terrain_indices.append(vert.index)
    group.add(terrain_indices, 1.0, "REPLACE")

    obj["hg_role"] = ROLE_TEMPLATE

    # Label anchor: Empty at underside center, parented to the template.
    anchor: bpy.types.Object = bpy.data.objects.new("HG_LABEL_ANCHOR", None)
    anchor.empty_display_type = "PLAIN_AXES"
    anchor.location = (0.0, 0.0, -h)
    bpy.context.scene.collection.objects.link(anchor)
    anchor.parent = obj
    anchor["hg_role"] = ROLE_LABEL_ANCHOR

    return obj


def build_gradient_heightmap(path: Path) -> None:
    """Write a synthetic linear-in-x grayscale gradient PNG to ``path``.

    Pixel (u, v) has value round(u / (W-1) * 255) / 255 in R=G=B, so the
    raster is a known linear gradient in the x direction.
    """
    width: int = GRADIENT_WIDTH
    height: int = GRADIENT_HEIGHT
    image: bpy.types.Image = bpy.data.images.new(
        name="hg_gradient", width=width, height=height, alpha=False
    )
    pixels: list[float] = [0.0] * (width * height * 4)
    for v in range(height):
        for u in range(width):
            value: float = round(u / (width - 1) * 255) / 255.0
            idx: int = (v * width + u) * 4
            pixels[idx] = value
            pixels[idx + 1] = value
            pixels[idx + 2] = value
            pixels[idx + 3] = 1.0
    image.pixels = pixels
    image.filepath_raw = str(path)
    image.file_format = "PNG"
    image.save()
    bpy.data.images.remove(image)


def cleanup_scene() -> None:
    """Remove all objects and orphan mesh data (test isolation)."""
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for mesh in list(bpy.data.meshes):
        if mesh.users == 0:
            bpy.data.meshes.remove(mesh)
