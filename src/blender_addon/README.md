# Hex Heightmap Generator (Blender extension)

Batch-generate printable, heightmapped hex tiles from a single user-authored
template, a local heightmap raster, and a list of cube coordinates (`q,r,s`).

For each requested coordinate the extension:

1. Deep-copies the template object **and** its mesh datablock (the source
   template is never modified).
2. Deforms **only** the designated terrain surface (a vertex group) in Z from
   the corresponding region of the heightmap raster.
3. Engraves the `q,r,s` coordinate label on the underside via a Boolean
   Difference, then removes the temporary text cutter.
4. Records `hg_q`, `hg_r`, `hg_s`, `hg_source_template`, and
   `hg_role = generated_tile` custom properties on the new object.

Every generated tile owns an independent mesh datablock. A failed tile is
cleaned up and never corrupts the template or previously generated tiles.

## Requirements

- **Blender 5.x** (developed and tested against **5.2.0 LTS**). The manifest
  declares `blender_version_min = "5.0.0"`.
- No third-party Python dependencies. The extension uses only `bpy`, `bmesh`,
  `mathutils`, and the Python standard library.

## Install

1. Build the installable ZIP (from `src/blender_addon`):

   ```powershell
   python scripts/package.py
   ```

   This produces `dist/hex_heightmap_generator-0.1.0.zip` containing
   `blender_manifest.toml` and the `hex_heightmap_generator/` package at the
   ZIP root.

2. In Blender: **Edit > Preferences > Extensions > Install from Disk** and
   select the ZIP. Enable **Hex Heightmap Generator** if it is not enabled
   automatically.

3. Open the **3D Viewport > Sidebar (N) > Hex Generator** tab.

## Workflow

1. **Template.** Model (or generate) a hex tile whose local +Z is "up".
   - Select the template object, then **Set From Active Object**.
   - Enter Edit Mode, select the terrain-surface faces, then
     **Set Terrain Surface** (stores them in the `HG_TERRAIN_SURFACE` vertex
     group).
   - Place the 3D Cursor at the desired underside label center, then
     **Create / Move Label Anchor** (creates a parented `HG_LABEL_ANCHOR`
     Empty).
2. **Heightmap.** Point **File** at a local grayscale raster (PNG/EXR). Set
   orientation, raster origin, pixels-per-unit, and the elevation range/offset
   in millimetres.
3. **Tiles.** Paste one `q,r,s` coordinate per line, then **Generate Tiles**.
   Inspect the new `HG_GENERATED` collection. **Clear Generated Tiles** removes
   only generated tiles (it never deletes unknown user objects).

### Sample template

To avoid hand-modelling a template, generate a ready-to-use one:

```powershell
blender --background --python scripts/create_sample_template.py -- dist/sample_template.blend
```

This writes a hexagonal-prism template (concentric-hexagon tessellated top,
terrain vertex group, underside label anchor) to `dist/sample_template.blend`.
Open it in Blender and use it directly, or model your own.

## Development

The package is self-contained under `src/blender_addon/`. Pure modules
(`coordinates`, `sampling`, `naming`, `validation`) are `bpy`-free and are
unit-tested with normal Python; `bpy`-dependent modules are tested through a
Blender background-mode harness.

### Environment

```powershell
cd src/blender_addon
python -m venv env
.\env\Scripts\Activate.ps1
pip install -e ".[dev]"
```

### Tests

```powershell
# Pure unit tests (fast, no Blender required)
pytest tests/unit/

# Blender integration tests (background-mode harness)
& "D:\SteamLibrary\steamapps\common\Blender\blender.exe" --background --python scripts/run_integration.py

# End-to-end dry run (sample template -> 10 tiles -> clear)
& "D:\SteamLibrary\steamapps\common\Blender\blender.exe" --background --python scripts/verify_end_to_end.py
```

### Lint / type check

```powershell
ruff check .
ruff format --check .
pyright
```

The code is held to **pyright strict** with zero errors. `bpy`-dependent files
carry a per-file `# pyright:` pragma that relaxes only the diagnostics that
Blender's untyped C API cannot satisfy (missing imports/stubs, unknown member
types, etc.); the pure core modules are fully strict with no pragmas.

## Layout

```text
src/blender_addon/
  hex_heightmap_generator/
    blender_manifest.toml     # Blender extension manifest
    __init__.py               # lazy registration shim (no top-level bpy import)
    properties.py             # Scene PropertyGroup (scene.hg_settings)
    ui.py                     # N-panel (3D Viewport > Sidebar > Hex Generator)
    operators_setup.py        # set template / terrain surface / label anchor
    operators_generate.py     # batch orchestration + generate/clear operators
    operators_hello.py        # hello-world operator (toolchain gate)
    coordinates.py            # q,r,s parse/validate + cube/axial/plane transforms
    sampling.py               # bilinear sampler on a normalized [0,1] grid
    heightmap.py              # raster load + grayscale verification
    mesh_ops.py               # deep-copy + Z deformation + Boolean helper
    label.py                  # coordinate label engraving (FONT -> mesh -> Boolean)
    validation.py             # preflight (parse + bounds + name collision)
    naming.py                 # deterministic object/collection names
  tests/
    unit/                     # pure-module tests (plain pytest)
    integration/              # bpy tests (Blender background harness)
  scripts/
    package.py                # build the installable extension ZIP
    run_integration.py        # Blender background-mode test harness
    create_sample_template.py # generate a ready-to-use sample template .blend
    verify_end_to_end.py      # end-to-end dry run (design doc §19.3)
```

## Documented deviations from the design doc

1. **Tests live outside the package.** The design doc's suggested layout nests
   `tests/` inside `hex_heightmap_generator/`. In practice the tests are kept
   in a sibling `tests/` directory so the shippable package (and the built ZIP)
   contains only runtime code. `scripts/package.py` excludes `tests/`, `env/`,
   `dist/`, and bytecode from the ZIP.
2. **`sampling.py` is split out of `heightmap.py`.** The design doc lists a
   single `heightmap.py` for "image load, pixel bulk read, normalization,
   bilinear sampling." The bilinear sampler is `bpy`-free and is isolated in
   `sampling.py` so it can be unit-tested with normal Python; `heightmap.py`
   handles the `bpy`-dependent raster load and grayscale verification.

## Design reference

See [`docs/blender_hex_heightmap_addon_design.md`](../../docs/blender_hex_heightmap_addon_design.md)
for the full design, validation rules, error/transaction model, and acceptance
criteria.
