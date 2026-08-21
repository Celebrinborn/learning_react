"""Mesh operations: deep-copy, terrain deformation, Boolean helper.

Deep-copy and deformation use direct datablock access (no bpy.ops) so
batch generation and headless tests are straightforward (design doc §22).
The template is never modified; each tile owns an independent mesh.
"""

# pyright: reportMissingImports=none, reportMissingModuleSource=none, reportMissingTypeStubs=none, reportUnknownMemberType=none, reportUnknownVariableType=none, reportUnknownArgumentType=none, reportUnknownParameterType=none, reportUntypedBaseClass=none

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import bmesh
import bpy

from hex_heightmap_generator.coordinates import CubeCoord, cube_to_plane
from hex_heightmap_generator.heightmap import Heightmap
from hex_heightmap_generator.naming import GROUP_TERRAIN_SURFACE, tile_object_name
from hex_heightmap_generator.sampling import bilinear_sample, normalized_to_elevation
from hex_heightmap_generator.validation import MappingParams, plane_to_pixel

BooleanOperation = Literal["DIFFERENCE", "UNION"]
BooleanSolver = Literal["EXACT", "FLOAT"]


@dataclass(frozen=True)
class BooleanResult:
    """Structured success/failure result for a Boolean operation (§9.2)."""

    success: bool
    message: str = ""


def _terrain_vertex_indices(obj: bpy.types.Object) -> set[int]:
    """Return the set of vertex indices in the terrain-surface group."""
    group: bpy.types.VertexGroup | None = obj.vertex_groups.get(GROUP_TERRAIN_SURFACE)
    if group is None:
        return set()
    indices: set[int] = set()
    for vertex in obj.data.vertices:
        for group_entry in vertex.groups:
            if group_entry.group == group.index and group_entry.weight > 0.0:
                indices.add(vertex.index)
                break
    return indices


def _recalculate_normals(mesh: bpy.types.Mesh) -> None:
    """Recalculate all face normals to point outward."""
    bm: bmesh.types.BMesh = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()


def generate_tile(
    template: bpy.types.Object,
    collection: bpy.types.Collection,
    coord: CubeCoord,
    heightmap: Heightmap,
    mapping: MappingParams,
    terrain_base_z: float,
    elevation_offset_mm: float,
    elevation_range_mm: float,
) -> bpy.types.Object:
    """Generate one terrain-deformed tile for ``coord``.

    Deep-copies the template object and mesh datablock (never a linked
    duplicate), deforms only the terrain-surface vertices in Z from the
    heightmap, and links the result into ``collection``. The template is
    left unchanged.
    """
    tile_obj: bpy.types.Object = template.copy()
    tile_obj.data = template.data.copy()
    tile_obj.name = tile_object_name(coord)
    collection.objects.link(tile_obj)

    terrain_indices: set[int] = _terrain_vertex_indices(tile_obj)
    center_x, center_y = cube_to_plane(coord, mapping.orientation, mapping.hex_radius)

    mesh: bpy.types.Mesh = tile_obj.data
    for vertex in mesh.vertices:
        if vertex.index not in terrain_indices:
            continue
        sample_x: float = center_x + vertex.co.x
        sample_y: float = center_y + vertex.co.y
        u, v = plane_to_pixel(sample_x, sample_y, mapping)
        normalized: float = bilinear_sample(
            heightmap.grid, heightmap.width, heightmap.height, u, v
        )
        vertex.co.z = terrain_base_z + normalized_to_elevation(
            normalized, elevation_offset_mm, elevation_range_mm
        )

    _recalculate_normals(mesh)
    return tile_obj


def apply_boolean(
    target: bpy.types.Object,
    operand: bpy.types.Object,
    operation: BooleanOperation,
    solver: BooleanSolver = "EXACT",
) -> BooleanResult:
    """Apply a Boolean operation to ``target`` using ``operand``.

    Both DIFFERENCE and UNION are supported behind this one helper so
    future stamps (raised labels, sockets, rocks) need no second code
    path (§9.2). The operand must already be a mesh. This function owns
    temporary modifier cleanup and deletes the operand on success.
    Returns a structured result rather than only raising.
    """
    if target.type != "MESH" or operand.type != "MESH":
        return BooleanResult(False, "target and operand must be mesh objects")

    modifier: bpy.types.BooleanModifier = target.modifiers.new(
        name="HG_BOOLEAN", type="BOOLEAN"
    )
    modifier.operation = operation
    modifier.solver = solver
    modifier.object = operand

    depsgraph: bpy.types.Depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated: bpy.types.Object = target.evaluated_get(depsgraph)
    if evaluated is None:
        target.modifiers.remove(modifier)
        return BooleanResult(False, "failed to evaluate Boolean result")

    new_mesh: bpy.types.Mesh = bpy.data.meshes.new_from_object(
        evaluated, preserve_all_data_layers=False, depsgraph=depsgraph
    )
    old_mesh: bpy.types.Mesh = target.data
    target.data = new_mesh
    target.modifiers.remove(modifier)
    if old_mesh.users == 0:
        bpy.data.meshes.remove(old_mesh)

    # Clean up the operand (it has served its purpose).
    operand_data: bpy.types.Mesh = operand.data
    bpy.data.objects.remove(operand, do_unlink=True)
    if operand_data.users == 0:
        bpy.data.meshes.remove(operand_data)

    if len(target.data.vertices) == 0:
        return BooleanResult(False, "Boolean produced an empty mesh")
    return BooleanResult(True)
