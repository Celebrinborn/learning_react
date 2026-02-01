# Hex Grid Implementation Proposal

## Overview

This proposal outlines the implementation of a **3km hex grid overlay** on the campaign map, using **axial coordinates** (based on [Red Blob Games' guide](https://www.redblobgames.com/grids/hexagons/)). The grid will serve as the foundational spatial reference system for linking events, objects, and encounters to specific locations.

---

## Coordinate System Choice: **Axial (q, r)**

Based on the Red Blob Games guide, I recommend **axial coordinates** because:

| Feature | Axial | Offset | Cube |
|---------|-------|--------|------|
| Vector operations (add/subtract) | ✅ | ❌ | ✅ |
| Simple algorithms | ✅ | Some | ✅ |
| Storage efficiency | ✅ (2 values) | ✅ | ❌ (3 values) |
| Easy neighbor calculation | ✅ | Complex | ✅ |

The third cube coordinate `s` can be derived when needed: `s = -q - r`

### Orientation: **Pointy-Top** (North/South points)

```
    /\          Pointy sides face North and South
   /  \         Flat edges face East and West
  /    \
  \    /
   \  /
    \/
```

---

## Grid Geometry (3km hexes)

For **pointy-top** hexes with a circumradius of **1.5km** (center to corner):

| Property | Formula | Value |
|----------|---------|-------|
| **Size (circumradius)** | Given | 1,500m (1.5km) |
| **Width** | `√3 × size` | ~2,598m |
| **Height** | `2 × size` | 3,000m |
| **Horizontal spacing** | `width` | ~2,598m |
| **Vertical spacing** | `3/4 × height` | 2,250m |

> **Note:** A 3km "hex" typically refers to the distance across the flat edges (height for pointy-top), so `size = 1.5km`.

---

## Data Model

### Backend: New Models

#### `HexCoordinate` (Value Object)
```python
class HexCoordinate(BaseModel):
    """Axial coordinate for a hex cell"""
    q: int
    r: int
    
    @property
    def s(self) -> int:
        """Cube coordinate s (derived)"""
        return -self.q - self.r
```

#### `HexCell` (Database Entity)
```python
class TerrainType(str, Enum):
    UNDEFINED = "undefined"
    FOREST = "forest"
    MOUNTAIN = "mountain"
    PLAINS = "plains"
    WATER = "water"
    SWAMP = "swamp"
    DESERT = "desert"
    TUNDRA = "tundra"
    URBAN = "urban"
    # ... extensible

class HexCell(BaseModel):
    """A single hex cell in the grid"""
    id: str  # Format: "layer_{layer_id}_q_{q}_r_{r}" e.g., "layer_0_q_0_r_0"
    q: int
    r: int
    layer_id: int = 0  # Layer 0 = ground level
    terrain_type: TerrainType = TerrainType.UNDEFINED
    created_at: datetime
    updated_at: datetime
    
class HexCellCreate(BaseModel):
    q: int
    r: int
    layer_id: int = 0
    terrain_type: TerrainType = TerrainType.UNDEFINED

class HexCellUpdate(BaseModel):
    terrain_type: Optional[TerrainType] = None
```

#### Origin Point
**Haden** (lat: 61.238408, lon: 7.712059) will be designated as hex `(q=0, r=0)` - the origin of the grid.

---

### Frontend: New Types

```typescript
// types/hexGrid.ts

export type TerrainType = 
  | 'undefined'
  | 'forest'
  | 'mountain'
  | 'plains'
  | 'water'
  | 'swamp'
  | 'desert'
  | 'tundra'
  | 'urban';

export interface HexCoordinate {
  q: number;
  r: number;
}

export interface HexCell {
  id: string;
  q: number;
  r: number;
  layer_id: number;
  terrain_type: TerrainType;
  created_at: string;
  updated_at: string;
}

export interface HexCellCreate {
  q: number;
  r: number;
  layer_id?: number;
  terrain_type?: TerrainType;
}
```

---

## Coordinate Conversion Functions

### Pixel (Lat/Lng) to Hex

```typescript
// Constants
const HEX_SIZE = 1500; // meters (circumradius)
const ORIGIN_LAT = 61.238408; // Haden
const ORIGIN_LNG = 7.712059;

// Meters per degree (approximate at this latitude)
const METERS_PER_DEG_LAT = 111320;
const METERS_PER_DEG_LNG = 111320 * Math.cos(ORIGIN_LAT * Math.PI / 180); // ~55,800m

function latLngToHex(lat: number, lng: number): HexCoordinate {
  // Convert lat/lng to meters from origin
  const x = (lng - ORIGIN_LNG) * METERS_PER_DEG_LNG;
  const y = (lat - ORIGIN_LAT) * METERS_PER_DEG_LAT;
  
  // Pointy-top pixel to hex (inverted matrix)
  const q = (Math.sqrt(3)/3 * x - 1/3 * y) / HEX_SIZE;
  const r = (2/3 * y) / HEX_SIZE;
  
  return hexRound({ q, r });
}

function hexToLatLng(q: number, r: number): [number, number] {
  // Pointy-top hex to pixel
  const x = HEX_SIZE * (Math.sqrt(3) * q + Math.sqrt(3)/2 * r);
  const y = HEX_SIZE * (3/2 * r);
  
  // Convert meters to lat/lng
  const lat = ORIGIN_LAT + y / METERS_PER_DEG_LAT;
  const lng = ORIGIN_LNG + x / METERS_PER_DEG_LNG;
  
  return [lat, lng];
}
```

### Hex Rounding (for fractional coordinates)

```typescript
function hexRound(hex: { q: number; r: number }): HexCoordinate {
  const s = -hex.q - hex.r;
  
  let q = Math.round(hex.q);
  let r = Math.round(hex.r);
  let s_rounded = Math.round(s);
  
  const q_diff = Math.abs(q - hex.q);
  const r_diff = Math.abs(r - hex.r);
  const s_diff = Math.abs(s_rounded - s);
  
  if (q_diff > r_diff && q_diff > s_diff) {
    q = -r - s_rounded;
  } else if (r_diff > s_diff) {
    r = -q - s_rounded;
  }
  
  return { q, r };
}
```

---

## Hex Polygon Generation (for rendering)

```typescript
function hexCorners(centerLat: number, centerLng: number): [number, number][] {
  const corners: [number, number][] = [];
  
  for (let i = 0; i < 6; i++) {
    // Pointy-top: angles at 30°, 90°, 150°, 210°, 270°, 330°
    const angleDeg = 60 * i + 30;
    const angleRad = angleDeg * Math.PI / 180;
    
    const dx = HEX_SIZE * Math.cos(angleRad);
    const dy = HEX_SIZE * Math.sin(angleRad);
    
    const lat = centerLat + dy / METERS_PER_DEG_LAT;
    const lng = centerLng + dx / METERS_PER_DEG_LNG;
    
    corners.push([lat, lng]);
  }
  
  return corners;
}
```

---

## API Endpoints

### Backend Routes

```python
# routes/hex_grid.py

# GET /api/hex-cells?layer_id=0&min_q=-10&max_q=10&min_r=-10&max_r=10
# Returns hex cells in the given range

# GET /api/hex-cells/{layer_id}/{q}/{r}
# Returns a specific hex cell (creates with defaults if doesn't exist)

# PUT /api/hex-cells/{layer_id}/{q}/{r}
# Updates a hex cell (terrain_type, etc.)

# GET /api/hex-cells/at-location?lat={lat}&lng={lng}&layer_id=0
# Returns the hex cell containing the given coordinates
```

---

## Frontend Components

### New Components

1. **`HexGridOverlay.tsx`** - Renders the hex grid as SVG polygons on Leaflet
2. **`HexCellPopup.tsx`** - Shows hex info on click (coordinates, terrain, linked events)
3. **`TerrainPicker.tsx`** - UI for selecting terrain type

### Integration with Map.tsx

```tsx
<MapContainer>
  {/* Existing layers */}
  <LayersControl>
    {/* Add new overlay */}
    <LayersControl.Overlay checked name="Hex Grid (3km)">
      <HexGridOverlay 
        layerId={0}
        visible={true}
        onHexClick={handleHexClick}
      />
    </LayersControl.Overlay>
  </LayersControl>
</MapContainer>
```

---

## Layer System (Future-Ready)

| Layer ID | Name | Description |
|----------|------|-------------|
| 0 | Ground | Physical terrain (only layer for now) |
| 1 | Underground | Caves, dungeons (future) |
| 2 | Aerial | Sky regions (future) |
| 3+ | Custom | User-defined layers (future) |

---

## File Structure

```
src/backend/src/
├── models/
│   └── hex_grid.py          # HexCoordinate, HexCell, TerrainType
├── routes/
│   └── hex_grid.py          # API endpoints
├── storage/
│   └── hex_grid.py          # HexGridStorage class
└── interfaces/
    └── hex_grid.py          # IHexGridStorage interface

src/frontend/src/
├── types/
│   └── hexGrid.ts           # TypeScript types
├── services/
│   └── hexGridService.ts    # API client
├── components/map/
│   ├── HexGridOverlay.tsx   # Main grid renderer
│   ├── HexCell.tsx          # Individual hex polygon
│   └── TerrainPicker.tsx    # Terrain selection UI
└── utils/
    └── hexMath.ts           # Coordinate math functions
```

---

## Implementation Phases

### Phase 1: Core Infrastructure
- [ ] Backend models (`HexCoordinate`, `HexCell`, `TerrainType`)
- [ ] Backend storage (file-based, matching existing pattern)
- [ ] Backend routes (CRUD for hex cells)
- [ ] Frontend types and hex math utilities
- [ ] Basic hex grid overlay component

### Phase 2: Visual Rendering
- [ ] Render visible hexes based on map viewport
- [ ] Terrain-based coloring/styling
- [ ] Click-to-select hex interaction

### Phase 3: Data Integration (Future)
- [ ] Link `MapLocation` to `HexCell`
- [ ] Link events/encounters to hex coordinates
- [ ] Multi-layer support

---

## Open Questions

1. **Grid extent**: Should we pre-generate hexes or create them on-demand?
   - **Recommendation**: On-demand creation (lazy initialization)

2. **Performance**: For large viewports, how many hexes should we render?
   - **Recommendation**: Only render hexes visible in current viewport + small buffer

3. **Persistence**: Store all hex cells or only modified ones?
   - **Recommendation**: Only store hexes with non-default data

---

## Summary

This implementation uses **axial coordinates with pointy-top orientation** centered on Haden (0,0). Each hex represents a **3km area** and includes a terrain type. The layer system (starting with layer 0 for ground) provides future extensibility for underground/aerial regions.
