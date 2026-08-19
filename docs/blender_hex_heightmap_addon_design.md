# Blender Hex Heightmap Batch Generator
Design & Implementation Specification — Proof of Concept v0.1
Target: Blender 5.x (5.2.0 LTS) | Python add-on/extension | Single-material printable geometry

## 1. Executive summary
Build a Blender add-on that treats one user-authored hex tile as an immutable template. The user marks which surface region is terrain, marks where an engraved tile label belongs, selects a source heightmap, and supplies a newline-delimited list of cube coordinates (q,r,s). The add-on generates one independent mesh object per requested coordinate, deforms only the designated terrain surface from the corresponding heightmap region, engraves the coordinate label with Boolean Difference, and leaves the source template unchanged.
This first version deliberately excludes multi-material/color output, roads, rivers, texture painting, procedural scenery, network downloads, and automatic slicer integration. The goal is to validate the core coordinate-to-terrain-to-printable-mesh pipeline with the fewest moving parts.
## 2. Non-negotiable behavior
- The base hex object is never modified by generation.
- Every generated tile owns an independent mesh datablock; generated tiles must not share mutable mesh data with the template or with each other.
- The terrain source is user-supplied and local for v0.1. Generation must not depend on Internet access.
- Each coordinate line is exactly three signed integers q,r,s and must satisfy q + r + s = 0.
- A failed tile does not corrupt the template or previously generated tiles.
- Generated tile names are deterministic from q,r,s.
- The label is cut into the generated tile with Boolean Difference. Additive Boolean Union support should exist as a small reusable internal primitive, but v0.1 does not require a user-facing additive stamp.
- All geometric quantities are interpreted in millimeters after Blender scene-unit normalization.
## 3. Target platform and rationale
| Item | Decision | Reason |
| --- | --- | --- |
| Blender | 5.x (5.2.0 LTS) | Stable LTS API target; `blender_version_min = "5.0.0"` covers the 5.x line. |
| Language | Python using bpy + bmesh | Native add-on stack; no external runtime required. |
| UI | 3D Viewport > Sidebar (N-panel) | Keeps setup and batch generation next to the model. |
| Terrain raster | Local 16-bit grayscale PNG or OpenEXR preferred; TIFF accepted if Blender loads it | Sufficient precision for height data without adding GDAL as an MVP dependency. |
| Output | Generated Blender mesh objects; optional STL export as a later v0.1.x feature | First validate the meshes visually and with Blender before adding more file-format behavior. |

## 4. User workflow
1. Open or create a .blend file containing the finished base hex.
1. Select the base hex object.
1. Enter Edit Mode and select the top face(s) that are allowed to receive terrain elevation.
1. Press Set Terrain Surface. The add-on stores the selected vertices in a vertex group named HG_TERRAIN_SURFACE and records the template object.
1. Place the 3D Cursor at the desired center of the underside label and orient the template so local +Z is 'up'. Press Create Label Anchor. The add-on creates an Empty named HG_LABEL_ANCHOR parented to the template.
1. Choose the local heightmap file and define its mapping parameters.
1. Paste q,r,s coordinates into the batch text box, one tile per line.
1. Press Validate. Resolve any input/template errors.
1. Press Generate Tiles.
1. Inspect the new HG_GENERATED collection. The template remains intact.
## 5. Blender scene contract
The add-on should use explicit object metadata instead of relying only on object names. Names are for human readability; custom properties are the authoritative associations.
| Scene element | Required representation | Required custom data / semantics |
| --- | --- | --- |
| Base hex | Mesh Object | ["hg_role"] = "template"; source of all copies |
| Terrain surface | Vertex Group on base hex | Name: HG_TERRAIN_SURFACE; contains all vertices allowed to move in Z |
| Label anchor | Empty Object | ["hg_role"] = "label_anchor"; parent = template; local transform defines label position/orientation |
| Heightmap | Blender Image datablock loaded from local file | File path plus mapping settings stored on Scene PropertyGroup |
| Generated tiles | Mesh Objects in HG_GENERATED collection | ["hg_role"] = "generated_tile"; q, r, s custom integer properties |
| Temporary label cutter | Temporary Text/Curve -> Mesh object | Created per tile, Boolean-applied, then deleted |

## 6. Data sources and read operations
The term 'data source' below means every external or Blender-resident input the generator reads. The implementation should centralize reads so generation logic receives normalized data rather than reaching into UI state ad hoc.
### 6.1 Source A — base hex mesh
Source: bpy.types.Object selected and stored as the template object.
- Read object.type and reject anything other than MESH.
- Read object.matrix_world only for placement; perform terrain math in template-local coordinates.
- Read object.data.vertices, polygons, edges, and bounding box.
- Read the HG_TERRAIN_SURFACE vertex group membership to determine deformable vertices.
- Before each tile, create both an object copy and mesh-data copy. Do not use a linked duplicate.
```text
tile_obj = template.copy()
tile_obj.data = template.data.copy()
generated_collection.objects.link(tile_obj)
```

### 6.2 Source B — terrain-surface selection
Set Terrain Surface is a setup-time write operation. It reads the currently selected mesh vertices/faces in Edit Mode and writes membership to HG_TERRAIN_SURFACE. Generation later reads only the vertex group.
- When invoked from face-select mode, collect every vertex belonging to any selected face.
- Replace the existing group contents rather than appending stale vertices.
- Reject an empty selection.
- Warn if selected vertices include the bottom face or side walls, but do not attempt heuristic repair.
- Store a setup checksum/count so Validate can warn if the template topology changed after setup.
### 6.3 Source C — label anchor
The label anchor is an Empty parented to the template. Its local transform is the stable location/orientation for text placement. Generation reads matrix_local from the anchor, then applies the copied tile's world transform.
- Create Label Anchor at the current 3D Cursor position.
- Default orientation: text lies parallel to the XY plane and extrudes along local Z.
- Default intended use: underside engraving. The user may rotate the Empty manually if needed.
- Do not infer the bottom face every generation; the explicit anchor removes ambiguity.
### 6.4 Source D — heightmap raster
Primary v0.1 source: a user-selected local raster loaded as a Blender Image datablock. Preferred formats are 16-bit grayscale PNG or OpenEXR. Height values are treated as data, not display color.
- Load using bpy.data.images.load(path, check_existing=True).
- Set/expect the image colorspace to Non-Color where available.
- Read image.size for width and height.
- Bulk-read pixel values into Python memory once per generation batch; do not repeatedly index Image.pixels per vertex if avoidable.
- For grayscale images, use the R channel. For RGB images, require R=G=B within tolerance or explicitly document that R is authoritative.
- Normalize raw sample to [0,1], then convert to model elevation with the configured vertical mapping.
- Use bilinear interpolation for sub-pixel samples.
- Never resize or resample the source Image datablock destructively.
Recommended height conversion:
```text
height_mm = elevation_offset_mm + normalized_sample * elevation_range_mm
vertex_local_z = terrain_base_z_mm + height_mm
```

For the MVP, the heightmap is intentionally non-geospatial: its pixels are simply a planar data grid. If the user starts from a GeoTIFF/DEM, preprocess it to a grayscale raster first or use one of the optional DEM acquisition sources in section 15.
### 6.5 Source E — q,r,s coordinate list
Input is a multiline StringProperty. Parsing is strict and deterministic. Accept comma-separated integers; optionally tolerate whitespace around commas. One nonblank line equals one tile.
```text
0,0,0
1,-1,0
1,0,-1
2,-1,-1
```

- Ignore blank lines.
- Reject lines that do not contain exactly three integer fields.
- Reject coordinates where q+r+s != 0.
- Reject duplicate coordinates in the same request by default; report the duplicate line numbers.
- Canonical display/label format for MVP: q,r,s, e.g. 2,-1,-1.
- Canonical object-name format: HG_q+2_r-1_s-1 (sanitize minus signs only as needed for Blender naming).
### 6.6 Source F — add-on settings
| Setting | Type | Default | Meaning |
| --- | --- | --- | --- |
| Hex orientation | Enum | POINTY | Pointy-top or flat-top coordinate-to-plane mapping. |
| Hex center spacing X/Y | Float or derived | Derived | Physical center-to-center spacing in template-local units. |
| Raster origin pixel | Float2 | (0,0) | Pixel coordinate corresponding to cube coordinate (0,0,0) center. |
| Pixels per hex X/Y | Float2 | User-set | Scale from hex-plane coordinates to raster pixels. |
| Raster Y direction | Enum | DOWN | Whether increasing local Y maps toward increasing or decreasing image-row index. |
| Elevation range mm | Float | 10.0 | Physical vertical range represented by normalized 0..1. |
| Elevation offset mm | Float | 0.0 | Constant physical vertical offset. |
| Label depth mm | Float | 0.6 | Boolean cutter penetration below the target surface. |
| Label size mm | Float | 4.0 | Approximate text character height. |
| Boolean solver | Enum | EXACT | Use Exact for label cut robustness. |

## 7. Coordinate-to-heightmap mapping
This mapping is the most important mathematical contract in the add-on. Do not encode it implicitly in object placement. Cube coordinates are first converted to a 2D hex-center coordinate, then converted to raster pixels.
### 7.1 Cube to axial
Use q and r as axial coordinates; s is validation/redundancy only because s = -q-r.
### 7.2 Axial to 2D hex center
For a pointy-top hex with hex radius R (center to corner):
```text
x = R * sqrt(3) * (q + r/2)
y = R * 3/2 * r
```

For a flat-top hex:
```text
x = R * 3/2 * q
y = R * sqrt(3) * (r + q/2)
```

The implementation should not assume the physical template is positioned at these world coordinates. These formulas define a logical map plane. The template's measured radius or explicit user-entered spacing is used only as a scale reference.
### 7.3 2D center to raster pixels
```text
pixel_x = raster_origin_x + x * pixels_per_model_unit_x
pixel_y = raster_origin_y + y * pixels_per_model_unit_y * raster_y_sign
```

For each deformable vertex, add that vertex's local XY offset from the tile center before converting to raster pixel space. This means adjacent tiles sample the same underlying continuous raster and should meet at matching elevations along shared edges.
```text
sample_plane_x = tile_center_x + vertex_local_x
sample_plane_y = tile_center_y + vertex_local_y
u_px, v_px = plane_to_pixel(sample_plane_x, sample_plane_y)
h = bilinear_sample(raster, u_px, v_px)
```

## 8. Terrain deformation algorithm
1. Duplicate template object and mesh datablock.
1. Resolve deformable vertex indices from the copied HG_TERRAIN_SURFACE group.
1. Compute logical map center for q,r,s.
1. For each deformable vertex, convert its local XY position plus tile-center map offset to raster pixel coordinates.
1. Bilinearly sample normalized height.
1. Convert normalized height to physical Z.
1. Write only vertex.co.z. Keep vertex X and Y unchanged.
1. Update mesh and recalculate normals.
1. Do not apply displacement to side/bottom vertices unless they are explicitly in HG_TERRAIN_SURFACE.
Important consequence: the template must already contain enough terrain-surface tessellation for the desired print detail. v0.1 should validate vertex density but should not automatically subdivide, because automatic subdivision can alter perimeter topology and complicate edge matching. A future version may provide a controlled subdivision/setup operator.
## 9. Label generation and Boolean operations
### 9.1 Engraved q,r,s label
1. Create a temporary FONT object containing the canonical q,r,s string.
1. Apply configured text size/alignment; center around the label anchor.
1. Extrude the text sufficiently to cross the tile surface by label_depth_mm plus a small safety margin.
1. Convert the text/curve to a mesh.
1. Transform the cutter to the copied tile using the label anchor transform.
1. Create a Boolean modifier on the tile using operation DIFFERENCE and solver EXACT.
1. Evaluate/apply the modifier.
1. Delete the temporary cutter object and data.
1. Verify that the resulting tile is still a mesh and that the Boolean operation did not return an empty or obviously invalid result.
Exact Boolean is the requested default because Blender documents it as the slower, more robust solver, including better handling of difficult/coplanar cases. The stamp should intentionally penetrate beyond the target face instead of merely touching it.
### 9.2 Generic Boolean helper for future use
Implement Boolean Difference and Boolean Union behind one internal function even though v0.1 only exposes Difference. This keeps future raised labels, sockets, rocks, roads, or other geometry stamps from requiring a second code path.
```text
apply_boolean(target, operand, operation: Literal["DIFFERENCE", "UNION"], solver="EXACT")
```

- Operand must be a mesh before modifier application.
- Target and operand transforms must be resolved consistently before applying.
- Function owns temporary modifier cleanup.
- Function returns a structured success/failure result rather than only throwing.
## 10. Generated-object lifecycle
Generation is intentionally destructive on generated copies and non-destructive on the template.
```text
HG_TEMPLATE
HG_LABEL_ANCHOR

HG_GENERATED/
    HG_q+0_r+0_s+0
    HG_q+1_r-1_s+0
    HG_q+1_r+0_s-1
```

- Create HG_GENERATED automatically if absent.
- On name collision, default behavior is fail that coordinate with a clear message rather than silently replacing an existing tile.
- Provide a separate Clear Generated Tiles operator scoped only to objects with hg_role == generated_tile in HG_GENERATED.
- Do not delete unknown user objects even if they happen to be inside HG_GENERATED.
- Every generated tile receives integer custom properties hg_q, hg_r, hg_s plus hg_source_template.
## 11. User interface
Panel location: 3D Viewport > Sidebar > Hex Generator.
```text
HEX GENERATOR

Template
  Template: [Object picker]
  [Set From Active Object]
  [Set Terrain Surface]
  [Create / Move Label Anchor]

Heightmap
  File: [path]
  Orientation: [Pointy / Flat]
  Raster origin X: [...]
  Raster origin Y: [...]
  Pixels per model unit X: [...]
  Pixels per model unit Y: [...]
  Elevation range: [...] mm
  Elevation offset: [...] mm

Label
  Size: [...] mm
  Depth: [...] mm

Tiles
  [multiline q,r,s input]

  [Validate]
  [Generate Tiles]
  [Clear Generated Tiles]

Status
  Template: OK
  Terrain vertices: 4096
  Heightmap: 8192 x 8192
  Requested: 10
  Errors: 0
```

## 12. Validation rules
| Validation | Severity | Required response |
| --- | --- | --- |
| No template selected / object is not MESH | Error | Block generation. |
| Template shares mesh data with another object | Warning | Allowed; generation still deep-copies mesh data. |
| Missing HG_TERRAIN_SURFACE | Error | Block generation. |
| Terrain vertex group empty | Error | Block generation. |
| Missing label anchor | Error | Block generation for MVP. |
| Heightmap cannot be loaded | Error | Block generation. |
| Any sample required outside raster bounds | Error by default | List affected q,r,s; do not clamp silently. |
| Malformed or invalid cube coordinate | Error | Report line number and value. |
| Duplicate requested coordinate | Error | Report both line numbers. |
| Existing generated object with same q,r,s | Error for that tile | Do not overwrite. |
| Low terrain vertex density | Warning | State approximate max XY vertex spacing. |
| Template transforms have non-unit scale | Warning | Recommend Apply Scale; generation should use local-space math consistently. |

## 13. Add-on architecture
Suggested package layout:
```text
hex_heightmap_generator/
    blender_manifest.toml
    __init__.py
    properties.py
    ui.py
    operators_setup.py
    operators_generate.py
    coordinates.py
    heightmap.py
    mesh_ops.py
    label.py
    validation.py
    naming.py
    tests/
        test_coordinates.py
        test_parser.py
        test_height_sampling.py
        test_naming.py
```

| Module | Responsibility |
| --- | --- |
| properties.py | Scene/add-on PropertyGroups and enum definitions. |
| ui.py | N-panel only; no geometry logic. |
| operators_setup.py | Set template, terrain group, label anchor. |
| operators_generate.py | Batch orchestration, progress, per-tile error isolation. |
| coordinates.py | q,r,s parse/validate and cube/axial/plane transforms. |
| heightmap.py | Image load, pixel bulk read, normalization, bilinear sampling. |
| mesh_ops.py | Deep-copy template, vertex deformation, Boolean helper, mesh cleanup. |
| label.py | Coordinate-string formatting and temporary text cutter creation. |
| validation.py | Preflight validation returning structured issues. |
| naming.py | Deterministic object/collection names. |

## 14. Setup and development instructions
### 14.1 User setup
1. Install Blender 5.x (5.2.0 LTS).
1. Build/package the extension as a ZIP containing blender_manifest.toml and the Python package.
1. In Blender Preferences > Add-ons/Extensions, use Install from Disk and select the ZIP.
1. Enable Hex Heightmap Generator if installation does not enable it automatically.
1. Open the 3D Viewport Sidebar and choose the Hex Generator tab.
1. Set Scene units so modeling is consistent; the add-on should display dimensions in millimeters and warn when the template scale is unapplied.
### 14.2 Developer setup
- Develop against Blender 5.x (5.2.0 LTS), not the system Python interpreter.
- Avoid third-party Python dependencies in v0.1. Use bpy, bmesh, mathutils, Python stdlib, and Blender image loading.
- Keep pure coordinate/parser/sampling functions free of bpy where practical so they can be unit-tested with normal Python.
- For integration testing, run Blender in background mode with a temporary .blend fixture and execute a Python test harness.
- Do not make core generation depend on bpy.ops selection/context where direct data API access is practical; operators are acceptable where Blender requires them (for example some conversion/application flows), but isolate context-dependent code.
### 14.3 Extension manifest
Use the current Blender extension/add-on packaging model. Minimum conceptual manifest:
```text
schema_version = "1.0.0"
id = "hex_heightmap_generator"
version = "0.1.0"
name = "Hex Heightmap Generator"
tagline = "Batch-generate printable heightmapped hex tiles"
maintainer = "Project owner"
type = "add-on"
blender_version_min = "5.0.0"
license = ["SPDX:GPL-3.0-or-later"]
```

The build agent must verify exact manifest keys against the Blender 5.x extension documentation before packaging; the above is the intended contract, not permission to guess around a packaging error.
## 15. Optional real-world elevation data sources
These are acquisition sources only. The MVP does not call them. If real geography is desired, download/preprocess the DEM to a local raster, then feed that raster to the add-on. This preserves deterministic/offline generation.
| Source | Coverage / resolution | When to use | Preprocessing into MVP input |
| --- | --- | --- | --- |
| Copernicus DEM GLO-30 | Global, 30 m DSM | Recommended global default when 30 m is sufficient. | Download the needed DEM tile(s), crop/mosaic externally, normalize the desired elevation interval into 16-bit grayscale or EXR. |
| NASA SRTMGL1 v3 | Near-global ~30 m; approx. 60°N to 56°S | Simple, well-known fallback or reproducible historical terrain source. | Acquire GeoTIFF/HGT, crop/mosaic, then normalize to local raster used by the add-on. |
| USGS 3DEP | United States; often 1 m DEM products where available | Preferred for high-resolution U.S. terrain. | Download 1 m DEM/OPR data, reproject/crop as needed, normalize to local raster. |
| OpenTopography | Portal/API exposing SRTM and many higher-resolution datasets | Convenient acquisition layer when dataset coverage permits. | Download selected raster; treat OpenTopography as acquisition, not a runtime dependency. |

## 16. External reference sources for the build agent
The agent should treat official Blender documentation as authoritative for Blender API behavior. External elevation sources are authoritative only for acquisition metadata. URLs are included so implementation can re-check current signatures.
- Blender 5.2 LTS release/support: https://www.blender.org/download/releases/5-2/
- Blender Python API — Object operators: https://docs.blender.org/api/5.2/bpy.ops.object.html
- Blender Python API — BooleanModifier: https://docs.blender.org/api/current/bpy.types.BooleanModifier.html
- Blender Python API — BMesh module: https://docs.blender.org/api/current/bmesh.html
- Blender Python API — BMesh operators: https://docs.blender.org/api/current/bmesh.ops.html
- Blender Python API — Object type: https://docs.blender.org/api/current/bpy.types.Object.html
- Blender Python API — MeshVertex: https://docs.blender.org/api/current/bpy.types.MeshVertex.html
- Blender Manual — add-ons/extensions installation: https://docs.blender.org/manual/en/latest/editors/preferences/addons.html
- Blender Manual — extension getting started: https://docs.blender.org/manual/en/latest/advanced/extensions/getting_started.html
- Copernicus DEM documentation: https://documentation.dataspace.copernicus.eu/APIs/SentinelHub/Data/DEM.html
- NASA Earthdata SRTMGL1: https://www.earthdata.nasa.gov/data/catalog/lpcloud-srtmgl1-003
- USGS 3DEP program: https://www.usgs.gov/3d-elevation-program
- OpenTopography SRTM Global: https://portal.opentopography.org/datasetMetadata?otCollectionID=OT.042013.4326.1
## 17. Error handling and transaction model
- Preflight the full batch before creating any geometry when possible.
- Generation then runs per tile. A per-tile exception must be caught, recorded, and followed by cleanup of that tile's temporary objects.
- If a tile fails after its copied object is created, delete that incomplete generated object unless a developer/debug flag says to retain failures.
- Do not roll back already completed tiles because a later coordinate fails.
- At completion, show counts: requested, succeeded, failed, skipped.
- Use Blender's undo integration at the operator level, but do not rely on undo as the primary safety mechanism; the template immutability is the safety mechanism.
## 18. Performance expectations
- Load and cache the raster once per batch.
- Parse and validate coordinate input once.
- Avoid bpy context switching inside the per-vertex loop.
- Prefer direct mesh coordinate writes and bulk data access where practical.
- 10 tiles is the initial proof-of-concept target. The design should not make 100 tiles architecturally impossible, but no optimization beyond obvious batch caching is required for v0.1.
- Show Blender progress reporting during batch generation so a large mesh does not appear frozen.
## 19. Test plan and acceptance criteria
### 19.1 Pure unit tests
- Parser accepts signed integers and whitespace.
- Parser rejects missing/excess fields, decimals, junk text, duplicate coordinates, and q+r+s != 0.
- Cube/axial-to-plane coordinate formulas match known fixture values.
- Bilinear sampler returns exact corner pixels and expected midpoint averages.
- Out-of-bounds samples return a structured error, not implicit clamping.
- Object-name formatting is deterministic for positive, zero, and negative coordinates.
### 19.2 Blender integration fixture
Create a tiny deterministic test .blend or generate it from a test script: a hex prism whose top has a known regular grid, a label anchor on the underside, and a synthetic gradient heightmap.
- Generate q=0,r=0,s=0 and verify the source template's vertex coordinates are byte/logically unchanged.
- Verify generated tile mesh datablock is not template.data and not shared with another generated tile.
- Verify terrain vertices change Z according to the gradient while non-terrain vertices remain unchanged.
- Generate two adjacent tiles and verify corresponding shared-edge terrain samples agree within a small numeric tolerance.
- Verify engraved label exists by checking the Boolean result changes underside geometry and the cutter no longer remains in the scene.
- Verify 10 requested valid coordinates produce 10 generated tile objects plus the still-existing base tile.
- Verify a malformed line prevents generation during preflight.
- Verify one induced Boolean failure does not delete or modify successful earlier tiles.
### 19.3 Definition of done for v0.1
- Fresh Blender 5.x (5.2.0 LTS) install can install the packaged add-on from disk.
- User can configure a template using only the add-on UI plus normal selection/3D Cursor placement.
- User can select a local heightmap and enter mapping values.
- User can paste 10 valid q,r,s lines and obtain 10 distinct terrain-deformed, engraved mesh objects.
- Template remains unchanged after generation and after clearing generated tiles.
- Adjacent tiles generated from a continuous raster have matching height samples at corresponding shared-edge vertices.
- No generated tile shares its mesh datablock with the template or with another tile.
- All errors are surfaced in the UI/report; there are no silent coordinate clamps, silent overwrites, or silent malformed-line skips.
## 20. Explicitly out of scope for v0.1
- Multiple filament/material assignment or 3MF material metadata.
- Automatic AMS/Bambu Studio integration.
- Roads, rivers, buildings, forests, or other stamps beyond the coordinate label.
- Interactive texture painting.
- Automatic download from Copernicus, NASA, USGS, OpenTopography, or any other network source.
- GeoTIFF coordinate reference system handling inside Blender.
- Automatic reprojection/geodesy.
- Automatic terrain subdivision/remeshing.
- Automatic support/overhang analysis.
- Batch printer plate layout.
- Editing generated tiles and later syncing them back to the template.
## 21. Recommended next increments after proof of concept
1. Add explicit STL export per generated tile and batch output-directory handling.
1. Add optional automatic terrain-surface subdivision during setup with perimeter-preservation rules.
1. Add a generic user-facing stamp list using the already-internal UNION/DIFFERENCE Boolean helper.
1. Add 3MF and multiple-material body support.
1. Add terrain/feature painting only after the coordinate sampling and watertight export pipeline is proven.
## 22. Implementation notes for the coding agent
Favor boring, explicit code. The proof of concept should not use Geometry Nodes unless a Blender API limitation makes direct mesh deformation impractical. There is no need for a custom viewport drawing layer, modal click tool, GIS stack, or generalized procedural terrain framework yet. The success criterion is deterministic duplication + raster sampling + Z deformation + Boolean engraving while preserving the base mesh.
Where the Blender API offers both context-sensitive bpy.ops and direct datablock/BMesh access, prefer direct access for core logic. This makes batch generation and headless tests substantially easier. Isolate any unavoidable operator/context manipulation in small helpers.
