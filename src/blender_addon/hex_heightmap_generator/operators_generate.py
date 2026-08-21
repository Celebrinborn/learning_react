"""Batch generation orchestration + generate/clear operators (design doc §10, §17).

``run_batch`` is the core orchestration (per-tile isolation, name-collision
skip, custom props, label engraving). The operators are thin glue that read
their parameters from the scene settings PropertyGroup and report structured
outcomes.
"""

# pyright: reportMissingImports=none, reportMissingModuleSource=none, reportMissingTypeStubs=none, reportUnknownMemberType=none, reportUnknownVariableType=none, reportUnknownArgumentType=none, reportUnknownParameterType=none, reportUntypedBaseClass=none, reportOptionalMemberAccess=none, reportOptionalSubscript=none

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

import bpy
from bpy.types import Operator as OperatorType

from hex_heightmap_generator.coordinates import (
    CubeCoord,
    HexOrientation,
    Issue,
    parse_cube_coords,
)
from hex_heightmap_generator.heightmap import Heightmap, HeightmapError, load_heightmap
from hex_heightmap_generator.label import engrave_label, find_label_anchor
from hex_heightmap_generator.mesh_ops import generate_tile
from hex_heightmap_generator.naming import (
    COLLECTION_GENERATED,
    ROLE_GENERATED_TILE,
    tile_object_name,
)
from hex_heightmap_generator.validation import MappingParams, validate_batch

RasterYDirection = Literal["DOWN", "UP"]


@dataclass
class BatchResult:
    """Structured outcome of a batch generation (design doc §17)."""

    requested: int
    succeeded: int
    failed: int
    skipped: int
    issues: list[Issue] = field(default_factory=list)


def _get_or_create_collection() -> bpy.types.Collection:
    collection: bpy.types.Collection | None = bpy.data.collections.get(
        COLLECTION_GENERATED
    )
    if collection is None:
        collection = bpy.data.collections.new(COLLECTION_GENERATED)
        bpy.context.scene.collection.children.link(collection)
    return collection


def _cleanup_failed_tile(name: str, collection: bpy.types.Collection) -> None:
    """Remove an incomplete generated tile (design doc §17)."""
    obj: bpy.types.Object | None = collection.objects.get(name)
    if obj is None:
        return
    data = obj.data
    bpy.data.objects.remove(obj, do_unlink=True)
    if data is not None and getattr(data, "users", 1) == 0:
        bpy.data.meshes.remove(data)


def run_batch(
    template: bpy.types.Object,
    heightmap: Heightmap,
    mapping: MappingParams,
    collection: bpy.types.Collection,
    coords: list[CubeCoord],
    label_size_mm: float,
    label_depth_mm: float,
    terrain_base_z: float,
    elevation_offset_mm: float,
    elevation_range_mm: float,
) -> BatchResult:
    """Generate tiles for ``coords`` with per-tile error isolation.

    A name collision skips that tile (no overwrite). A per-tile exception
    is caught, recorded, and the incomplete tile is cleaned up. Earlier
    completed tiles are never rolled back (design doc §17).
    """
    succeeded: int = 0
    failed: int = 0
    skipped: int = 0
    issues: list[Issue] = []
    anchor: bpy.types.Object | None = find_label_anchor(template)

    for coord in coords:
        name: str = tile_object_name(coord)
        if collection.objects.get(name) is not None:
            skipped += 1
            issues.append(
                Issue(
                    "error",
                    "NAME_COLLISION",
                    f"{name} already exists; skipped (not overwriting)",
                )
            )
            continue
        try:
            tile: bpy.types.Object = generate_tile(
                template,
                collection,
                coord,
                heightmap,
                mapping,
                terrain_base_z=terrain_base_z,
                elevation_offset_mm=elevation_offset_mm,
                elevation_range_mm=elevation_range_mm,
            )
            tile["hg_q"] = coord.q
            tile["hg_r"] = coord.r
            tile["hg_s"] = coord.s
            tile["hg_source_template"] = template.name
            tile["hg_role"] = ROLE_GENERATED_TILE
            if anchor is not None:
                engrave_label(tile, anchor, coord, label_size_mm, label_depth_mm)
            succeeded += 1
        except Exception as exc:  # noqa: BLE001 - per-tile isolation
            failed += 1
            issues.append(Issue("error", "TILE_FAILED", f"{name}: {exc}"))
            _cleanup_failed_tile(name, collection)

    return BatchResult(
        requested=len(coords),
        succeeded=succeeded,
        failed=failed,
        skipped=skipped,
        issues=issues,
    )


class HexgenGenerateTiles(OperatorType):
    """Preflight then batch-generate tiles from the scene settings.

    Reads all parameters from ``context.scene.hg_settings`` (design doc
    §6.6, §11) rather than operator properties, since the template is an
    object picker that only a PropertyGroup can hold.
    """

    bl_idname: str = "hexgen.generate_tiles"
    bl_label: str = "Generate Tiles"
    bl_description: str = "Batch-generate terrain-deformed, engraved tiles"
    bl_options: set[str] = {"UNDO"}

    def execute(self, context: bpy.types.Context) -> set[str]:
        settings = context.scene.hg_settings
        template: bpy.types.Object | None = settings.template
        if template is None or template.type != "MESH":
            self.report({"ERROR"}, "No valid template selected")
            return {"CANCELLED"}

        coords, parse_issues = parse_cube_coords(settings.batch_text)
        if parse_issues:
            for issue in parse_issues:
                self.report({"ERROR"}, issue.message)
            return {"CANCELLED"}

        try:
            heightmap: Heightmap = load_heightmap(settings.heightmap_path)
        except HeightmapError as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}

        orientation: HexOrientation = (
            HexOrientation.POINTY
            if settings.orientation == "POINTY"
            else HexOrientation.FLAT
        )
        y_sign: float = 1.0 if settings.raster_y_direction == "DOWN" else -1.0
        mapping: MappingParams = MappingParams(
            raster_origin_x=settings.raster_origin_x,
            raster_origin_y=settings.raster_origin_y,
            pixels_per_unit_x=settings.pixels_per_unit_x,
            pixels_per_unit_y=settings.pixels_per_unit_y,
            raster_y_sign=y_sign,
            hex_radius=1.0,
            orientation=orientation,
        )

        collection: bpy.types.Collection = _get_or_create_collection()
        existing_names: set[str] = {o.name for o in collection.objects}
        issues: list[Issue] = validate_batch(
            settings.batch_text,
            heightmap.width,
            heightmap.height,
            mapping,
            existing_names,
        )
        # Parse and bounds errors block the whole batch; name collisions are
        # handled per-tile (skip) inside run_batch.
        blocking: list[Issue] = [i for i in issues if i.code != "NAME_COLLISION"]
        if blocking:
            for issue in blocking:
                self.report({"ERROR"}, issue.message)
            return {"CANCELLED"}

        result: BatchResult = run_batch(
            template,
            heightmap,
            mapping,
            collection,
            coords,
            settings.label_size_mm,
            settings.label_depth_mm,
            terrain_base_z=0.0,
            elevation_offset_mm=settings.elevation_offset_mm,
            elevation_range_mm=settings.elevation_range_mm,
        )
        for issue in result.issues:
            self.report({"WARNING"}, issue.message)
        self.report(
            {"INFO"},
            f"Generated {result.succeeded}/{result.requested} "
            f"(failed {result.failed}, skipped {result.skipped})",
        )
        return {"FINISHED"}


class HexgenClearGenerated(OperatorType):
    """Remove only generated tiles from HG_GENERATED (design doc §10)."""

    bl_idname: str = "hexgen.clear_generated"
    bl_label: str = "Clear Generated Tiles"
    bl_description: str = "Deletes only hg_role == generated_tile objects"
    bl_options: set[str] = {"UNDO"}

    def execute(self, context: bpy.types.Context) -> set[str]:
        collection: bpy.types.Collection | None = bpy.data.collections.get(
            COLLECTION_GENERATED
        )
        if collection is None:
            self.report({"INFO"}, "No generated tiles to clear")
            return {"FINISHED"}
        removed: int = 0
        for obj in list(collection.objects):
            if obj.get("hg_role") == ROLE_GENERATED_TILE:
                data = obj.data
                bpy.data.objects.remove(obj, do_unlink=True)
                if data is not None and getattr(data, "users", 1) == 0:
                    bpy.data.meshes.remove(data)
                removed += 1
        self.report({"INFO"}, f"Cleared {removed} generated tile(s)")
        return {"FINISHED"}


classes: tuple[type[OperatorType], ...] = (
    HexgenGenerateTiles,
    HexgenClearGenerated,
)


def register() -> None:
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
