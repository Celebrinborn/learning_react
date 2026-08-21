"""Build a ready-to-use sample template .blend for Hex Heightmap Generator.

Creates a hexagonal-prism template whose top face is tessellated with
concentric hexagon rings (a proven-watertight pattern that deforms well
under heightmap sampling and survives Boolean engraving), an
HG_TERRAIN_SURFACE vertex group on the top vertices, a label-anchor Empty
on the underside, and the hg_role custom properties — then saves the scene
to a .blend file. This removes the need to hand-model a template.

Usage (from src/blender_addon):
    blender --background --python scripts/create_sample_template.py -- out.blend

The output .blend contains exactly one template object (plus its parented
label anchor) and nothing else.
"""

# pyright: reportMissingImports=none, reportMissingModuleSource=none, reportMissingTypeStubs=none, reportUnknownMemberType=none, reportUnknownVariableType=none, reportUnknownArgumentType=none, reportUnknownParameterType=none, reportUntypedBaseClass=none, reportOptionalMemberAccess=none, reportOptionalSubscript=none

from __future__ import annotations

import math
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import bmesh
import bpy

from hex_heightmap_generator.naming import (
    GROUP_TERRAIN_SURFACE,
    ROLE_LABEL_ANCHOR,
    ROLE_TEMPLATE,
)

# Sample template geometry (model units).
HEX_RADIUS: float = 1.0
PRISM_HEIGHT: float = 2.0
# Number of concentric hexagon rings on the top face. The outer ring is the
# prism boundary; each inner ring is a scaled-down hexagon. More rings =
# more terrain detail. 1 = 7 vertices, 2 = 13, 3 = 19, ...
GRID_RINGS: int = 3


def _hex_angles() -> list[float]:
    """Pointy-top hexagon corner angles (radians): 90 + 60*k."""
    return [math.radians(90.0 + 60.0 * k) for k in range(6)]


def build_sample_template(name: str = "HG_TEMPLATE") -> bpy.types.Object:
    """Create the sample template object and return it.

    The top face is tessellated with ``GRID_RINGS`` concentric hexagon
    rings plus a center vertex. The outer ring coincides with the prism
    boundary so the side walls connect cleanly. The bottom is a flat fan.
    """
    bm: bmesh.types.BMesh = bmesh.new()
    angles: list[float] = _hex_angles()
    r: float = HEX_RADIUS
    h: float = PRISM_HEIGHT
    rings: int = max(1, GRID_RINGS)

    # Concentric hexagon rings, outermost (radius r) down to innermost.
    ring_verts: list[list[bmesh.types.BMVert]] = []
    for ring in range(rings, 0, -1):
        radius: float = r * ring / rings
        ring_verts.append(
            [
                bm.verts.new((radius * math.cos(a), radius * math.sin(a), 0.0))
                for a in angles
            ]
        )
    center: bmesh.types.BMVert = bm.verts.new((0.0, 0.0, 0.0))

    # Top face: center fan to the innermost ring, then quads between rings.
    innermost: list[bmesh.types.BMVert] = ring_verts[-1]
    for k in range(6):
        k1: int = (k + 1) % 6
        bm.faces.new((center, innermost[k], innermost[k1]))
    for ring_idx in range(len(ring_verts) - 1):
        outer: list[bmesh.types.BMVert] = ring_verts[ring_idx]
        inner: list[bmesh.types.BMVert] = ring_verts[ring_idx + 1]
        for k in range(6):
            k1: int = (k + 1) % 6
            bm.faces.new((inner[k], inner[k1], outer[k1], outer[k]))

    # Bottom: fan.
    bottom_outer: list[bmesh.types.BMVert] = []
    for a in angles:
        bottom_outer.append(bm.verts.new((r * math.cos(a), r * math.sin(a), -h)))
    bottom_center: bmesh.types.BMVert = bm.verts.new((0.0, 0.0, -h))
    for k in range(6):
        k1: int = (k + 1) % 6
        bm.faces.new((bottom_center, bottom_outer[k1], bottom_outer[k]))

    # Sides: quads between the outer top ring and the bottom ring.
    top_outer: list[bmesh.types.BMVert] = ring_verts[0]
    for k in range(6):
        k1: int = (k + 1) % 6
        bm.faces.new((top_outer[k], top_outer[k1], bottom_outer[k1], bottom_outer[k]))

    bm.normal_update()
    mesh: bpy.types.Mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()

    obj: bpy.types.Object = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)

    # Terrain surface = all top-face vertices (z == 0).
    group: bpy.types.VertexGroup = obj.vertex_groups.new(name=GROUP_TERRAIN_SURFACE)
    terrain_indices: list[int] = []
    for vert in mesh.vertices:
        if vert.co.z > -1e-6:
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


def main(argv: list[str]) -> int:
    """Parse args, build the template, save the .blend. Returns exit code.

    Blender passes the full command line in ``sys.argv``; the script's own
    arguments are those after the ``--`` separator.
    """
    if "--" in argv:
        args: list[str] = argv[argv.index("--") + 1 :]
    else:
        args = []
    if len(args) != 1:
        print(
            "Usage: blender --background --python "
            "scripts/create_sample_template.py -- out.blend",
            file=sys.stderr,
        )
        return 2
    out_path: Path = Path(args[0])
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Start from a clean scene.
    bpy.ops.wm.read_factory_settings(use_empty=True)
    build_sample_template()
    bpy.ops.wm.save_as_mainfile(filepath=str(out_path))
    print(f"Saved sample template: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
