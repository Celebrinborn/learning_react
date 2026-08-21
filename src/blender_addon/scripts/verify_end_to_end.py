"""Dry run of the manual end-to-end test (design doc §19.3).

Loads the sample template .blend, registers the extension, configures the
scene settings, generates 10 tiles, and verifies the outcomes:
- 10 distinct mesh tiles with custom props
- template intact (vertex count + coords unchanged)
- each tile has a unique mesh datablock
- Clear Generated removes only the generated tiles

Usage (from src/blender_addon):
    blender --background --python scripts/verify_end_to_end.py
"""

# pyright: reportMissingImports=none, reportMissingModuleSource=none, reportMissingTypeStubs=none, reportUnknownMemberType=none, reportUnknownVariableType=none, reportUnknownArgumentType=none, reportUnknownParameterType=none, reportUntypedBaseClass=none, reportOptionalMemberAccess=none, reportOptionalSubscript=none

from __future__ import annotations

from pathlib import Path
import sys
import tempfile

ADDON_ROOT: Path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ADDON_ROOT))

import bpy  # noqa: E402

from hex_heightmap_generator.naming import (  # noqa: E402
    COLLECTION_GENERATED,
    ROLE_GENERATED_TILE,
)

TEN_COORDS: str = "\n".join(
    [
        "0,0,0",
        "1,0,-1",
        "1,-1,0",
        "0,1,-1",
        "-1,0,1",
        "-1,1,0",
        "2,0,-2",
        "2,-1,-1",
        "0,-1,1",
        "-2,0,2",
    ]
)


def main() -> int:
    template_blend: Path = ADDON_ROOT / "dist" / "sample_template.blend"
    if not template_blend.is_file():
        print(f"FAIL: {template_blend} not found; run create_sample_template.py")
        return 1

    # Load the sample template scene.
    bpy.ops.wm.open_mainfile(filepath=str(template_blend))
    template: bpy.types.Object | None = bpy.data.objects.get("HG_TEMPLATE")
    if template is None:
        print("FAIL: HG_TEMPLATE not found in sample .blend")
        return 1

    # Register the extension.
    import hex_heightmap_generator  # noqa: PLC0415

    hex_heightmap_generator.register()

    # Build a gradient heightmap PNG.
    tmp: Path = Path(tempfile.mkdtemp(prefix="hg_e2e_"))
    png: Path = tmp / "g.png"
    width: int = 200
    height: int = 200
    image: bpy.types.Image = bpy.data.images.new(
        name="hg_e2e", width=width, height=height, alpha=False
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
    image.filepath_raw = str(png)
    image.file_format = "PNG"
    image.save()
    bpy.data.images.remove(image)

    # Configure scene settings.
    s = bpy.context.scene.hg_settings
    s.template = template
    s.heightmap_path = str(png)
    s.orientation = "POINTY"
    s.raster_origin_x = width / 2.0
    s.raster_origin_y = height / 2.0
    s.pixels_per_unit_x = 20.0
    s.pixels_per_unit_y = 20.0
    s.raster_y_direction = "DOWN"
    s.elevation_range_mm = 10.0
    s.elevation_offset_mm = 0.0
    s.label_size_mm = 4.0
    s.label_depth_mm = 0.6
    s.batch_text = TEN_COORDS

    before: list[tuple[float, float, float]] = [
        (v.co.x, v.co.y, v.co.z) for v in template.data.vertices
    ]

    result = bpy.ops.hexgen.generate_tiles()
    print(f"generate_tiles -> {result}")

    collection: bpy.types.Collection | None = bpy.data.collections.get(
        COLLECTION_GENERATED
    )
    tiles: list[bpy.types.Object] = (
        [o for o in collection.objects if o.get("hg_role") == ROLE_GENERATED_TILE]
        if collection is not None
        else []
    )
    mesh_tiles: list[bpy.types.Object] = [t for t in tiles if t.type == "MESH"]
    print(f"tiles: {len(tiles)} (mesh: {len(mesh_tiles)})")

    after: list[tuple[float, float, float]] = [
        (v.co.x, v.co.y, v.co.z) for v in template.data.vertices
    ]

    datablocks: set[int] = {id(t.data) for t in mesh_tiles}
    props_ok: bool = all(
        "hg_q" in t and "hg_r" in t and "hg_s" in t and "hg_source_template" in t
        for t in mesh_tiles
    )

    # Clear.
    bpy.ops.hexgen.clear_generated()
    remaining: list[bpy.types.Object] = (
        [o for o in collection.objects if o.get("hg_role") == ROLE_GENERATED_TILE]
        if collection is not None
        else []
    )

    checks: list[tuple[str, bool]] = [
        ("10 mesh tiles generated", len(mesh_tiles) == 10),
        ("template intact", before == after),
        ("unique datablocks", len(datablocks) == 10),
        ("custom props on all tiles", props_ok),
        ("clear removed all generated tiles", len(remaining) == 0),
    ]
    failed: bool = False
    for label, ok in checks:
        print(f"  {'PASS' if ok else 'FAIL'} {label}")
        if not ok:
            failed = True
    print("E2E RESULT:", "FAIL" if failed else "PASS")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
