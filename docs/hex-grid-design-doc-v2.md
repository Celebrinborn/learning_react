# Hex Grid Implementation Design (v2)

## Overview

This document defines the design for a **3-mile hex grid overlay** on the campaign map, using **cube coordinates (q, r, s)** (based on [Red Blob Games' guide](https://www.redblobgames.com/grids/hexagons/)). The grid serves as the foundational spatial reference system for linking notes, encounters, and campaign data to specific locations.

> **Document Status:** Design-only. Implementation and tests are deferred.

---

## Locked Design Decisions

The following are **non-negotiable** constraints for this system:

### Grid Metric

| Constant | Value | Description |
|----------|-------|-------------|
| `HEX_CENTER_SPACING_M` | 4828.032 | 3 miles in meters (center-to-center) |
| `HEX_SIZE_M` | ≈2787.0 | Circumradius (`HEX_CENTER_SPACING_M / √3`) |

**Key principle:** Moving to any adjacent hex always represents **exactly 3 miles of travel**.

### Origin

- **Haden** is the absolute origin:
  - Geographic: `lat=61.238408, lon=7.712059`
  - Hex coordinate: `(q=0, r=0, s=0)`
- All coordinate conversions are anchored to this point

### Non-Negotiables

| Rule | Rationale |
|------|-----------|
| No grid math in lat/lng degrees | Projection distortion makes degree-based math incorrect |
| No state mutation on `GET` | API purity; `GET` is always read-only |
| No duplicated rule definitions | Single source of truth in `data/terrain/terrain_types.json` |

---

## Coordinate System: Cube (q, r, s)

We use **cube coordinates** with all three values stored explicitly:

| Feature | Cube (q, r, s) | Axial (q, r) | Offset |
|---------|----------------|--------------|--------|
| Vector operations (add/subtract) | ✅ | ✅ | ❌ |
| Simple algorithms | ✅ | ✅ | Some |
| Hexagonal symmetry | ✅ | ❌ | ❌ |
| Easy neighbor calculation | ✅ | ✅ | Complex |
| Built-in parity check | ✅ | ❌ | ❌ |
| Readability | ✅ | Moderate | Low |

### Why Store All Three Coordinates?

1. **Parity checking**: The constraint `q + r + s = 0` validates coordinate integrity
2. **Readability**: All three axes are explicit
3. **Algorithm simplicity**: Distance, rotation, and reflection are elegant with all three coordinates

### Orientation: Pointy-Top (North/South Points)

```
    /\          Pointy sides face North and South
   /  \         Flat edges face East and West
  /    \
  \    /
   \  /
    \/
```

### Edge Numbering

For **pointy-top hexes**, edges are numbered **counterclockwise starting from East** (per Red Blob Games):

```
              N
             / \
        NW /     \ NE
       (2)/       \(1)
          |       |
      W   |       |   E
     (3)  |       |  (0)
          |       |
       (4)\       /(5)
        SW \     / SE
             \ /
              S
```

| Edge | Direction | Cube Vector (Δq, Δr, Δs) |
|------|-----------|---------------------------|
| 0    | East      | (+1, 0, -1) |
| 1    | Northeast | (+1, -1, 0) |
| 2    | Northwest | (0, -1, +1) |
| 3    | West      | (-1, 0, +1) |
| 4    | Southwest | (-1, +1, 0) |
| 5    | Southeast | (0, +1, -1) |

---

## Grid Geometry

For **pointy-top** hexes with **3 miles center-to-center**:

| Property | Formula | Value |
|----------|---------|-------|
| **Center-to-center** | Given | 3 miles (4,828.032m) |
| **Size (circumradius)** | `center_spacing / √3` | ≈1.732 miles (≈2,787m) |
| **Height (vertex-to-vertex)** | `2 × size` | ≈3.464 miles (≈5,575m) |
| **Horizontal spacing** | `center_spacing` | 3 miles (4,828m) |
| **Vertical spacing** | `3/4 × height` | ≈2.598 miles (≈4,181m) |

> **Key Insight:** "3 miles" refers to the distance between **hex centers**, not edge-to-edge. This simplifies travel calculations: every move to an adjacent hex = 3 miles.

---

## Stable Hex IDs

Every hex has a **canonical, deterministic ID** used in APIs, storage, and note linking.

### ID Format

```
hex:l{layer}:q{q}:r{r}:s{s}
```

### Examples

| Hex | ID |
|-----|-----|
| Origin (Haden) | `hex:l0:q0:r0:s0` |
| Layer 0, (3, -2, -1) | `hex:l0:q3:r-2:s-1` |
| Layer 1, (-5, 3, 2) | `hex:l1:q-5:r3:s2` |

### ID Properties

- **Stable**: IDs never change for a given coordinate
- **Deterministic**: Same inputs always produce same ID
- **Human-readable**: Can be parsed visually
- **Linkable**: Used for Obsidian-style note references

### ID Generation

ID generation must occur in **one canonical location** (backend model). Frontend and storage derive IDs by calling this function.

---

## Single Source of Truth: Terrain Types

### Location

```
data/terrain/terrain_types.json
```

This file is the **single authoritative definition** for all terrain types. Both backend and frontend consume this file (or an API-served copy). No hardcoded terrain tables in Python or TypeScript.

### Terrain Type Schema

```json
{
  "terrain_types": [
    {
      "id": "open",
      "display_name": "Open Terrain",
      "travel_time_seconds": 3600,
      "stealth_distance_table": [
        [20, -15],
        [40, -10],
        [80, -5],
        [160, 0],
        [320, 5],
        [640, 10],
        [null, 15]
      ],
      "navigation_difficulty": 5
    }
  ]
}
```

### Field Definitions

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Stable key (e.g., "open", "bog", "alpine") |
| `display_name` | string | Human-readable name |
| `travel_time_seconds` | int | Time to traverse one hex (3 miles) in seconds |
| `stealth_distance_table` | Array | `[max_distance_ft, modifier]` pairs; `null` = infinity |
| `navigation_difficulty` | int | DC modifier for getting lost (0 = auto-success) |

### Duration Representation

Durations are treated as time deltas, not wall-clock timestamps. Internally and over the API, durations are represented as integer seconds.

A structured `{hours, minutes, seconds}` form may be accepted or emitted for readability, but must always normalize to a single `total_seconds` value for computation.

**Canonical form:**

```json
{
  "total_seconds": 5400
}
```

**Why seconds (not milliseconds):**
- D&D time resolution is hours/minutes, not sub-second
- Travel, stealth, and navigation don't benefit from ms precision
- Seconds serialize cleanly and avoid accidental float math
- Easier to reason about when debugging

This is validated by Pydantic on the backend and parsed consistently on the frontend.

### Terrain Types (v1)

| ID | Display Name | Travel Time | Navigation DC |
|----|--------------|-------------|---------------|
| `undefined` | Undefined | 1h | 10 |
| `open` | Open Terrain | 1h | 5 |
| `light_cover` | Light Cover | 2h | 10 |
| `heavy_cover` | Heavy Cover | 3h | 15 |
| `bog` | Bog/Marsh | 3h | 15 |
| `alpine` | Alpine | 4h | 10 |
| `fjord` | Fjord | Impassable | N/A |
| `lake` | Lake | Impassable | N/A |
| `littoral` | Littoral | Impassable | N/A |
| `ocean` | Ocean | Impassable | N/A |
| `urban` | Urban | 1h | 0 (auto) |

> **Note:** Roads are NOT terrain types. Roads are graph edges that modify travel time when following them.

### Loading Strategy

1. **Backend**: Loads `terrain_types.json` at startup into Pydantic models
2. **Frontend**: Fetches terrain types via API endpoint (`GET /api/terrain-types`)
3. **Validation**: Backend validates terrain type references against loaded registry

---

## Implicit Hexes (Non-Persisted)

### Core Concept

The hex grid is **infinite by default**. Every valid coordinate resolves to a hex, whether or not it has been explicitly persisted.

### Behavior

| Scenario | Behavior |
|----------|----------|
| Hex has stored data | Return persisted hex |
| Hex has no stored data | Return implicit default hex |
| Implicit hex is modified | Persist on explicit update |

### Implicit Hex Properties

An implicit (non-persisted) hex has these default values:

| Property | Default Value |
|----------|---------------|
| `terrain_type` | `"undefined"` |
| `has_ford` | `false` |
| `is_persisted` | `false` |

### API Response Shape

```json
{
  "hex_id": "hex:l0:q3:r-2:s-1",
  "layer_id": 0,
  "q": 3,
  "r": -2,
  "s": -1,
  "is_persisted": false,
  "terrain_type": "undefined",
  "has_ford": false
}
```

### API Semantics

| Method | Behavior |
|--------|----------|
| `GET /api/hex-cells/{layer}/{q}/{r}/{s}` | Returns persisted hex OR implicit default. **Never mutates state.** |
| `PUT /api/hex-cells/{layer}/{q}/{r}/{s}` | Creates or replaces the persisted state of a hex cell |
| `PATCH /api/hex-cells/{layer}/{q}/{r}/{s}` | Partial update of specific fields on a persisted hex |
| `DELETE /api/hex-cells/{layer}/{q}/{r}/{s}` | Removes persisted hex (reverts to implicit) |

### Why Implicit Hexes?

1. **DM workflow**: Don't require pre-populating the entire map
2. **Infinite grid**: Any coordinate is valid (if parity check passes)
3. **Clean storage**: Only store hexes with meaningful modifications
4. **Consistent API**: Always returns a valid hex response

> **Note:** Hex IDs are designed to be externally referenceable (e.g., by documentation systems like Obsidian), but note storage and indexing are out of scope for this document.

---

## Projection-Correct Coordinate Conversion

### Problem with Degree-Based Math

Direct lat/lng arithmetic is **incorrect** for hex grid calculations:
- Latitude degrees have consistent meter spacing (~111km)
- Longitude degrees shrink toward poles (cos(lat) factor)
- This causes hex distortion at high latitudes

### Correct Approach: Projected Coordinates

All hex math must use **projected (meter-based) coordinates**:

1. Convert lat/lng → projected meters (using map's CRS)
2. Perform hex calculations in projected space
3. Convert back to lat/lng for rendering

### Coordinate Conversion Pipeline

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────┐
│   Lat/Lng   │ ──► │ Projected Meters │ ──► │ Hex (q,r,s) │
│  (WGS84)    │     │   (Leaflet CRS)  │     │   (Cube)    │
└─────────────┘     └──────────────────┘     └─────────────┘
```

### Required Utility Functions (Design-Level)

These functions will be implemented using Leaflet's projection system:

#### `latLngToHex(map, latlng) → HexCoordinate`

1. Use `map.project(latlng)` to get pixel/meter coordinates
2. Offset by origin (Haden) in projected space
3. Apply hex conversion matrix
4. Round to nearest valid hex

#### `hexToLatLng(map, q, r, s) → LatLng`

1. Validate parity (`q + r + s === 0`)
2. Apply inverse hex matrix to get projected offset
3. Add origin offset
4. Use `map.unproject()` to get lat/lng

#### `hexCorners(map, q, r, s) → LatLng[]`

1. Get hex center via `hexToLatLng()`
2. Calculate 6 corner offsets at proper angles (30°, 90°, 150°, etc.)
3. Apply offsets in projected space
4. Convert each corner back to lat/lng

### Origin Anchoring

All projected calculations are relative to Haden:
```
Origin (projected) = map.project(LatLng(61.238408, 7.712059))
Hex (0,0,0) center = Origin
```

### Local Linearization Assumption

All hex coordinates are defined in a local coordinate space anchored at hex (0,0,0), which corresponds to a fixed geographic location. Distances and directions are treated as locally linear relative to this origin.

This guarantees internal consistency (adjacent hex = 3 miles in game terms), even if the underlying map projection introduces distortion at large distances from the origin.

> **Key Principle:** The game model is authoritative; the map is representational. This design does not attempt to build a global geodesic system.

### Handling Negative Coordinates

Cube coordinates naturally support negatives:
- Hexes west of Haden have negative `q` values
- Hexes south of Haden have negative `r` values
- The `s` value is always `-q - r`

### Rounding Algorithm

When converting fractional hex coordinates to integers:

```
function hexRound(qFrac, rFrac):
    sFrac = -qFrac - rFrac
    
    q = round(qFrac)
    r = round(rFrac)
    s = round(sFrac)
    
    q_diff = abs(q - qFrac)
    r_diff = abs(r - rFrac)
    s_diff = abs(s - sFrac)
    
    # Reset component with largest error to maintain parity
    if q_diff > r_diff AND q_diff > s_diff:
        q = -r - s
    else if r_diff > s_diff:
        r = -q - s
    else:
        s = -q - r
    
    return (q, r, s)
```

---

## Rendering & Performance

### Zoom-Level Constraints

The hex grid should only render at appropriate zoom levels:

| Zoom Level | Behavior |
|------------|----------|
| < 10 | Grid hidden (too dense) |
| 10-12 | Show hex outlines only |
| 13+ | Full rendering with labels |

### Viewport Culling

Only render hexes within the current viewport plus a buffer:

1. Get viewport bounds from Leaflet
2. Convert corners to hex coordinates
3. Calculate bounding box in hex space
4. Add 1-2 hex buffer for smooth panning
5. Render only hexes in this range

### Geometry Caching

To improve performance:

1. **Cache hex polygons**: Once computed, reuse corner coordinates
2. **Layer grouping**: Use Leaflet layer groups for batch updates
3. **LOD (Level of Detail)**: Simplify rendering at lower zoom levels

### Estimated Hex Counts

| Viewport Size | Hexes Visible (approx) |
|---------------|------------------------|
| 10 miles | ~15 hexes |
| 50 miles | ~350 hexes |
| 100 miles | ~1,400 hexes |

---

## Storage Model (v1)

### Design Goals

1. **Simple**: Easy to understand and debug
2. **Future-safe**: Can migrate to chunked files or SQLite later
3. **Sparse**: Only store persisted hexes

### File Structure

```
data/
├── terrain/
│   └── terrain_types.json     # Single source of truth for terrain
├── hex_cells/
│   └── layer_0.json           # All persisted hexes for layer 0
├── roads/
│   └── {path_id}.json         # Road graph definitions
└── rivers/
    └── {path_id}.json         # River graph definitions
```

### Hex Cell Storage Format

`data/hex_cells/layer_0.json`:

```json
{
  "layer_id": 0,
  "hexes": {
    "hex:l0:q0:r0:s0": {
      "terrain_type": "urban",
      "has_ford": false,
      "updated_at": "2026-02-01T12:00:00Z"
    },
    "hex:l0:q1:r-1:s0": {
      "terrain_type": "open",
      "has_ford": false,
      "updated_at": "2026-02-01T12:30:00Z"
    }
  }
}
```

### Key Properties

| Property | Description |
|----------|-------------|
| Keyed by `hex_id` | Direct lookup by canonical ID |
| Sparse storage | Only persisted hexes are stored |
| Layer isolation | Each layer in separate file |
| Compact format | No redundant coordinate data in values |

### Storage Interface (Design)

```python
class IHexGridStorage(ABC):
    @abstractmethod
    def get(self, layer_id: int, q: int, r: int, s: int) -> Optional[HexCellData]:
        """Get persisted hex data, or None if not persisted"""
        pass
    
    @abstractmethod
    def save(self, layer_id: int, q: int, r: int, s: int, data: HexCellData) -> None:
        """Persist hex data"""
        pass
    
    @abstractmethod
    def delete(self, layer_id: int, q: int, r: int, s: int) -> bool:
        """Remove persisted hex, returns True if existed"""
        pass
    
    @abstractmethod
    def get_range(self, layer_id: int, min_q: int, max_q: int, 
                  min_r: int, max_r: int) -> dict[str, HexCellData]:
        """Get all persisted hexes in coordinate range"""
        pass
```

### Concurrency Assumption (v1)

The system assumes a single active editor. File-level concurrency, conflict resolution, and atomic update guarantees are intentionally deferred until after proof-of-concept validation.

### Future Migration Path

The storage abstraction allows later migration without API changes:

| Current (v1) | Future Options |
|--------------|----------------|
| Single JSON per layer | Chunked files by region |
| Local file storage | SQLite database |
| | Azure Blob Storage |

---

## Validation Rules

### Parity Rule

All hex coordinates must satisfy: `q + r + s = 0`

This is enforced at:
1. **Model construction** (Pydantic validator)
2. **API input validation** (before processing)
3. **ID generation** (ID only generated for valid coordinates)

### ID Generation

Hex IDs are generated in **one canonical location**:

```python
def generate_hex_id(layer_id: int, q: int, r: int, s: int) -> str:
    if q + r + s != 0:
        raise ValueError(f"Invalid parity: {q} + {r} + {s} != 0")
    return f"hex:l{layer_id}:q{q}:r{r}:s{s}"
```

### Model Definitions

- No mutable defaults (use `default_factory` for lists)
- All terrain type references validated against loaded registry
- Timestamps use ISO 8601 format

### Terrain File Validation

On startup, validate `terrain_types.json`:
1. All required fields present
2. `id` values are unique
3. Duration values are non-negative
4. Stealth tables are properly ordered

---

## API Endpoints (Design)

### Hex Cell Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/hex-cells/{layer}/{q}/{r}/{s}` | Get hex (persisted or implicit) |
| `PUT` | `/api/hex-cells/{layer}/{q}/{r}/{s}` | Create or replace hex (full update) |
| `PATCH` | `/api/hex-cells/{layer}/{q}/{r}/{s}` | Partial update of specific fields |
| `DELETE` | `/api/hex-cells/{layer}/{q}/{r}/{s}` | Remove persisted hex |
| `GET` | `/api/hex-cells?layer_id=0&min_q=&max_q=&min_r=&max_r=` | Get hexes in range |
| `GET` | `/api/hex-cells/at-location?lat=&lng=&layer_id=0` | Get hex containing point |

### Terrain Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/terrain-types` | Get all terrain type definitions |
| `GET` | `/api/terrain-types/{id}` | Get specific terrain type |

### Response Shapes

#### Hex Cell Response

```json
{
  "hex_id": "hex:l0:q3:r-2:s-1",
  "layer_id": 0,
  "q": 3,
  "r": -2,
  "s": -1,
  "is_persisted": true,
  "terrain_type": "open",
  "has_ford": false,
  "updated_at": "2026-02-01T12:00:00Z"
}
```

#### Terrain Type Response

```json
{
  "id": "open",
  "display_name": "Open Terrain",
  "travel_time_seconds": 3600,
  "stealth_distance_table": [[20, -15], [40, -10], [80, -5], [160, 0], [320, 5], [640, 10], [null, 15]],
  "navigation_difficulty": 5
}
```

---

## Graph Theory Foundation (Roads & Rivers)

The hex grid is fundamentally a **graph**:

- **Nodes** = Hex cells (identified by cube coordinates)
- **Edges** = Connections between adjacent hex centers (roads, rivers)

Each hex has up to 6 neighbors (directions 0-5). Edges connect nodes and have properties like traversal direction and type.

### Edge Types

| Type | Description | Storage | Traversal |
|------|-------------|---------|-----------|
| **Road** | Increases travel speed, navigation DC 0 | `data/roads/` | Bidirectional |
| **River** | Blocks land travel (barrier) | `data/rivers/` | Direction = flow |

### Path Model

Roads and rivers are stored as **named collections of edges**:

```json
{
  "id": "kings_road",
  "name": "King's Road",
  "type": "road",
  "layer_id": 0,
  "edges": [
    {
      "start": {"q": 3, "r": 3, "s": -6},
      "end": {"q": 4, "r": 2, "s": -6},
      "bidirectional": true
    }
  ]
}
```

### Layer Ownership

Each road or river file belongs to exactly one layer. All edges within the file implicitly reference that layer. This avoids accidental cross-layer edges.

### Adjacency Invariant

For every edge, `start` and `end` must be adjacent hexes (i.e., their cube coordinate delta must match one of the six neighbor vectors). This keeps the graph honest and simplifies future movement logic.

### Key Concepts

1. **Edges connect hex centers** - An edge represents movement from one hex center to an adjacent hex center
2. **Roads and rivers can share edges** - Both can traverse the same pair of hexes (running parallel)
3. **Bidirectional traversal** - Roads allow travel in either direction

---

## File Structure (Planned)

```
data/
├── terrain/
│   └── terrain_types.json       # Single source of truth
├── hex_cells/
│   └── layer_0.json             # Persisted hexes
├── roads/
│   └── {path_id}.json           # Road definitions
└── rivers/
    └── {path_id}.json           # River definitions

src/backend/src/
├── models/
│   └── hex_grid.py              # HexCoordinate, HexCell, Duration
├── routes/
│   └── hex_grid.py              # API endpoints
├── storage/
│   └── hex_grid.py              # Storage implementation
└── interfaces/
    └── hex_grid.py              # IHexGridStorage interface

src/frontend/src/
├── types/
│   └── hexGrid.ts               # TypeScript types (API response shapes only)
├── services/
│   └── hexGridService.ts        # API client
├── components/map/
│   ├── HexGridOverlay.tsx       # Grid renderer
│   ├── HexCell.tsx              # Individual hex
│   └── TerrainPicker.tsx        # Terrain selection
└── utils/
    └── hexMath.ts               # Coordinate utilities
```

---

## Explicitly Out of Scope (v1)

The following are **deferred** to future versions:

| Feature | Reason |
|---------|--------|
| River crossing logic | Requires complex zone calculations |
| River geometry slicing | Needs detailed edge intersection math |
| Underground/aerial layers | Layer 0 only for v1 |
| Storage chunking | Single file per layer is sufficient initially |
| Path (road/river) editing UI | Focus on hex grid first |
| Boat travel | Land travel only for v1 |
| Notes / Obsidian integration | Separate content system; hex grid only provides spatial addressing |
| Tests and implementation | This is a design-only pass |

These features are **designed for** but not **implemented in** v1. The data model and API support future extension.

---

## Summary

| Aspect | Decision |
|--------|----------|
| Coordinates | Cube (q, r, s) with parity check `q + r + s = 0` |
| Orientation | Pointy-top |
| Grid metric | 3 miles center-to-center (`HEX_CENTER_SPACING_M = 4828.032`) |
| Origin | Haden at (0, 0, 0) — `lat=61.238408, lon=7.712059` |
| IDs | Deterministic format: `hex:l{layer}:q{q}:r{r}:s{s}` |
| Terrain source | `data/terrain/terrain_types.json` (single source of truth) |
| Default hexes | Implicit (non-persisted) with `undefined` terrain |
| Storage | Sparse, single JSON per layer |
| Projection | Leaflet CRS, no degree-based math |
| API semantics | `GET` never mutates; persistence on `PUT`/`PATCH` |

This design is **foundational** for a long-running D&D campaign with Obsidian-style note integration. The focus is on **conceptual correctness and clarity**, with future extensibility built into the architecture.
