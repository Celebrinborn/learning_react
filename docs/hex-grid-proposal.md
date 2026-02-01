# Hex Grid Implementation Proposal

## Overview

This proposal outlines the implementation of a **3km hex grid overlay** on the campaign map, using **cube coordinates (q, r, s)** (based on [Red Blob Games' guide](https://www.redblobgames.com/grids/hexagons/)). The grid will serve as the foundational spatial reference system for linking events, objects, and encounters to specific locations.

---

## Coordinate System Choice: **Cube (q, r, s)**

We use **cube coordinates** with all three values stored explicitly:

| Feature | Cube (q, r, s) | Axial (q, r) | Offset |
|---------|----------------|--------------|--------|
| Vector operations (add/subtract) | ✅ | ✅ | ❌ |
| Simple algorithms | ✅ | ✅ | Some |
| Hexagonal symmetry | ✅ | ❌ | ❌ |
| Easy neighbor calculation | ✅ | ✅ | Complex |
| Built-in parity check | ✅ | ❌ | ❌ |
| Readability | ✅ | Moderate | Low |

### Why store all three coordinates?

1. **Parity checking**: The constraint `q + r + s = 0` serves as a validation/parity bit. If the sum is non-zero, the coordinate is invalid.
2. **Readability**: All three axes are explicit, making it easier to understand hex positions and directions.
3. **Algorithm simplicity**: Many algorithms (distance, rotation, reflection) are more elegant with all three coordinates available.

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

## Grid Geometry (3-mile hexes)

For **pointy-top** hexes with **3 miles edge-to-edge** (flat edge to flat edge):

| Property | Formula | Value |
|----------|---------|-------|
| **Edge-to-edge (width)** | Given | 3 miles (~4,828m) |
| **Size (circumradius)** | `width / √3` | ~1.732 miles (~2,787m) |
| **Height (vertex-to-vertex)** | `2 × size` | ~3.464 miles (~5,575m) |
| **Horizontal spacing** | `width` | 3 miles (~4,828m) |
| **Vertical spacing** | `3/4 × height` | ~2.598 miles (~4,181m) |

> **Note:** "Edge-to-edge" means the distance across the hex from one flat edge to the opposite flat edge (east-west for pointy-top). "Vertex-to-vertex" is the distance from top point to bottom point (north-south for pointy-top).

---

## Data Model

### Backend: New Models

#### `HexCoordinate` (Value Object)
```python
class HexCoordinate(BaseModel):
    """Cube coordinate for a hex cell"""
    q: int
    r: int
    s: int
    
    @model_validator(mode='after')
    def validate_parity(self) -> 'HexCoordinate':
        """Validate that q + r + s = 0 (parity check)"""
        if self.q + self.r + self.s != 0:
            raise ValueError(f'Invalid hex coordinate: q + r + s must equal 0, got {self.q + self.r + self.s}')
        return self
```

#### `TerrainType` (Pydantic Model with Subtypes)
```python
from typing import List, Tuple
from datetime import timedelta

# === Movement Speed Categories ===
# These define how long it takes to travel one league

class MovementCategory:
    """Movement speed categories - hours per league as timedelta"""
    EASY = timedelta(hours=1)       # Flat ground, roads, open terrain
    MODERATE = timedelta(hours=2)   # Light forest, rolling hills
    DIFFICULT = timedelta(hours=3)  # Heavy forest, mountains, bogs
    EXTREME = timedelta(hours=4)    # Alpine, scree, treeline
    IMPASSABLE = timedelta(hours=99)  # Water (on foot)

# === Visibility Categories ===
# These define the stealth distance tables

# Distance thresholds: List of (max_distance_ft, stealth_modifier)
VISIBILITY_OPEN: List[Tuple[float, int]] = [
    (20, -15),      # 0-20 ft: nearly impossible to hide
    (40, -10),      # 20-40 ft: trivial to spot
    (80, -5),       # 40-80 ft: easy to spot
    (160, 0),       # 80-160 ft: baseline
    (320, 5),       # 160-320 ft: difficult to spot
    (640, 10),      # 320-640 ft: very difficult
    (float('inf'), 15),  # 640+ ft: nearly impossible to spot
]

VISIBILITY_LIGHT_COVER: List[Tuple[float, int]] = [
    (40, 0),        # 20-40 ft: baseline
    (80, 5),        # 40-80 ft: difficult to spot
    (160, 10),      # 80-160 ft: very difficult
    (float('inf'), 15),  # 160+ ft: nearly impossible
]

VISIBILITY_HEAVY_COVER: List[Tuple[float, int]] = [
    (10, 0),        # 5-10 ft: baseline
    (20, 5),        # 10-20 ft: difficult
    (40, 10),       # 20-40 ft: very difficult
    (float('inf'), 15),  # 40+ ft: nearly impossible
]

VISIBILITY_WATER: List[Tuple[float, int]] = [
    (float('inf'), -10),  # Very hard to hide on water
]

VISIBILITY_URBAN: List[Tuple[float, int]] = [
    (20, 0),        # Crowds provide some cover
    (40, 5),
    (80, 10),
    (float('inf'), 15),
]


class TerrainType(BaseModel):
    """Base terrain type with shared properties"""
    name: str
    base_travel_time: timedelta = MovementCategory.EASY  # Time to travel one league
    stealth_distance_table: List[Tuple[float, int]] = VISIBILITY_OPEN
    navigation_difficulty: int = 0  # How hard it is to get lost (higher = harder to navigate)
    
    class Config:
        frozen = True  # Immutable once created
        arbitrary_types_allowed = True  # Allow timedelta
    
    def get_stealth_modifier(self, distance_ft: float) -> int:
        """Get stealth modifier based on distance in feet"""
        for max_distance, modifier in self.stealth_distance_table:
            if distance_ft <= max_distance:
                return modifier
        # If beyond all thresholds, return the last modifier
        if self.stealth_distance_table:
            return self.stealth_distance_table[-1][1]
        return 0

class UndefinedTerrain(TerrainType):
    name: str = "undefined"
    base_travel_time: timedelta = MovementCategory.EASY
    stealth_distance_table: List[Tuple[float, int]] = VISIBILITY_OPEN
    navigation_difficulty: int = 10

# === Easy Movement + Open Visibility ===

class OpenTerrainTerrain(TerrainType):
    """Flat ground, open terrain, good trails"""
    name: str = "open_terrain"
    base_travel_time: timedelta = MovementCategory.EASY
    stealth_distance_table: List[Tuple[float, int]] = VISIBILITY_OPEN
    navigation_difficulty: int = 5  # Very Easy - can see landmarks

class RoadTerrain(TerrainType):
    """Well-maintained roads and paths"""
    name: str = "road"
    base_travel_time: timedelta = MovementCategory.EASY
    stealth_distance_table: List[Tuple[float, int]] = VISIBILITY_OPEN
    navigation_difficulty: int = 0  # Auto-success, just follow the road

# === Moderate Movement + Light Cover ===

class LightForestTerrain(TerrainType):
    """Light forest, rolling hills"""
    name: str = "light_forest"
    base_travel_time: timedelta = MovementCategory.MODERATE
    stealth_distance_table: List[Tuple[float, int]] = VISIBILITY_LIGHT_COVER
    navigation_difficulty: int = 10  # Easy - some cover obscures landmarks

class RollingHillsTerrain(TerrainType):
    """Rolling hills, gentle slopes"""
    name: str = "rolling_hills"
    base_travel_time: timedelta = MovementCategory.MODERATE
    stealth_distance_table: List[Tuple[float, int]] = VISIBILITY_LIGHT_COVER
    navigation_difficulty: int = 10  # Easy - hills can look similar

# === Difficult Movement + Heavy Cover ===

class HeavyForestTerrain(TerrainType):
    """Heavy forest, dense woodland"""
    name: str = "heavy_forest"
    base_travel_time: timedelta = MovementCategory.DIFFICULT
    stealth_distance_table: List[Tuple[float, int]] = VISIBILITY_HEAVY_COVER
    navigation_difficulty: int = 15  # Medium - hard to see sky or landmarks

class JungleTerrain(TerrainType):
    """Dense jungle vegetation"""
    name: str = "jungle"
    base_travel_time: timedelta = MovementCategory.DIFFICULT
    stealth_distance_table: List[Tuple[float, int]] = VISIBILITY_HEAVY_COVER
    navigation_difficulty: int = 20  # Hard - very disorienting

class SwampTerrain(TerrainType):
    """Swamp, flooded forests"""
    name: str = "swamp"
    base_travel_time: timedelta = MovementCategory.DIFFICULT
    stealth_distance_table: List[Tuple[float, int]] = VISIBILITY_HEAVY_COVER
    navigation_difficulty: int = 20  # Hard - confusing, paths change

# === Difficult Movement + Light Cover ===

class MountainTerrain(TerrainType):
    """Mountain terrain, steep slopes"""
    name: str = "mountain"
    base_travel_time: timedelta = MovementCategory.DIFFICULT
    stealth_distance_table: List[Tuple[float, int]] = VISIBILITY_LIGHT_COVER
    navigation_difficulty: int = 15  # Medium - ravines and ridges confuse

class BogTerrain(TerrainType):
    """Bogs, marshes, wetlands"""
    name: str = "bog"
    base_travel_time: timedelta = MovementCategory.DIFFICULT
    stealth_distance_table: List[Tuple[float, int]] = VISIBILITY_LIGHT_COVER
    navigation_difficulty: int = 15  # Medium - featureless, deceptive ground

# === Extreme Movement + Open Visibility ===

class AlpineTerrain(TerrainType):
    """Alpine slopes, treeline, snowfields"""
    name: str = "alpine"
    base_travel_time: timedelta = MovementCategory.EXTREME
    stealth_distance_table: List[Tuple[float, int]] = VISIBILITY_OPEN
    navigation_difficulty: int = 10  # Easy - open but weather can change fast

class ScreeTerrain(TerrainType):
    """Scree fields, loose rock"""
    name: str = "scree"
    base_travel_time: timedelta = MovementCategory.EXTREME
    stealth_distance_table: List[Tuple[float, int]] = VISIBILITY_OPEN
    navigation_difficulty: int = 10  # Easy - monotonous but visible

# === Special Terrain ===

class WaterTerrain(TerrainType):
    """Lakes, rivers, ocean (impassable on foot)"""
    name: str = "water"
    base_travel_time: timedelta = MovementCategory.IMPASSABLE
    stealth_distance_table: List[Tuple[float, int]] = VISIBILITY_WATER
    navigation_difficulty: int = 0  # N/A on foot

class UrbanTerrain(TerrainType):
    """Towns, cities, settlements"""
    name: str = "urban"
    base_travel_time: timedelta = MovementCategory.EASY
    stealth_distance_table: List[Tuple[float, int]] = VISIBILITY_URBAN
    navigation_difficulty: int = 0  # Auto-success - signs, people to ask

# Registry for looking up terrain by name
TERRAIN_TYPES: dict[str, TerrainType] = {
    "undefined": UndefinedTerrain(),
    "open_terrain": OpenTerrainTerrain(),
    "road": RoadTerrain(),
    "light_forest": LightForestTerrain(),
    "rolling_hills": RollingHillsTerrain(),
    "heavy_forest": HeavyForestTerrain(),
    "jungle": JungleTerrain(),
    "mountain": MountainTerrain(),
    "bog": BogTerrain(),
    "swamp": SwampTerrain(),
    "alpine": AlpineTerrain(),
    "scree": ScreeTerrain(),
    "water": WaterTerrain(),
    "urban": UrbanTerrain(),
}

def get_terrain_type(name: str) -> TerrainType:
    """Get terrain type by name, defaults to undefined"""
    return TERRAIN_TYPES.get(name, TERRAIN_TYPES["undefined"])
```

#### `HexCell` (Database Entity)
```python
class HexCell(BaseModel):
    """A single hex cell in the grid"""
    id: str  # Format: "layer_{layer_id}_q_{q}_r_{r}_s_{s}" e.g., "layer_0_q_0_r_0_s_0"
    q: int
    r: int
    s: int
    layer_id: int = 0  # Layer 0 = ground level
    terrain_type: str = "undefined"  # Terrain name (looked up via TERRAIN_TYPES registry)
    created_at: datetime
    updated_at: datetime
    
    @model_validator(mode='after')
    def validate_parity(self) -> 'HexCell':
        """Validate that q + r + s = 0 (parity check)"""
        if self.q + self.r + self.s != 0:
            raise ValueError(f'Invalid hex coordinate: q + r + s must equal 0, got {self.q + self.r + self.s}')
        return self
    
    def get_terrain(self) -> TerrainType:
        """Get the full terrain type object with properties"""
        return get_terrain_type(self.terrain_type)
    
class HexCellCreate(BaseModel):
    q: int
    r: int
    s: int
    layer_id: int = 0
    terrain_type: str = "undefined"
    
    @model_validator(mode='after')
    def validate_parity(self) -> 'HexCellCreate':
        if self.q + self.r + self.s != 0:
            raise ValueError(f'Invalid hex coordinate: q + r + s must equal 0, got {self.q + self.r + self.s}')
        return self

class HexCellUpdate(BaseModel):
    terrain_type: Optional[str] = None
```

#### Origin Point
**Haden** (lat: 61.238408, lon: 7.712059) will be designated as hex `(q=0, r=0)` - the origin of the grid.

---

### Frontend: New Types

```typescript
// types/hexGrid.ts

// Terrain type names (stored in HexCell)
export type TerrainTypeName = 
  | 'undefined'
  | 'open_terrain'
  | 'road'
  | 'light_forest'
  | 'rolling_hills'
  | 'heavy_forest'
  | 'jungle'
  | 'mountain'
  | 'bog'
  | 'swamp'
  | 'alpine'
  | 'scree'
  | 'water'
  | 'urban';

// === Movement Speed Categories ===
// Stored as milliseconds for easy math (hours * 60 * 60 * 1000)
export const MovementCategory = {
  EASY: 1 * 60 * 60 * 1000,       // 1 hour per league
  MODERATE: 2 * 60 * 60 * 1000,   // 2 hours per league
  DIFFICULT: 3 * 60 * 60 * 1000,  // 3 hours per league
  EXTREME: 4 * 60 * 60 * 1000,    // 4 hours per league
  IMPASSABLE: 99 * 60 * 60 * 1000, // Effectively impassable on foot
} as const;

// === Visibility Categories ===
// Distance threshold entry: [maxDistanceFt, stealthModifier]
type StealthDistanceEntry = [number, number];

const VISIBILITY_OPEN: StealthDistanceEntry[] = [
  [20, -15],      // 0-20 ft: nearly impossible to hide
  [40, -10],      // 20-40 ft: trivial to spot
  [80, -5],       // 40-80 ft: easy to spot
  [160, 0],       // 80-160 ft: baseline
  [320, 5],       // 160-320 ft: difficult to spot
  [640, 10],      // 320-640 ft: very difficult
  [Infinity, 15], // 640+ ft: nearly impossible to spot
];

const VISIBILITY_LIGHT_COVER: StealthDistanceEntry[] = [
  [40, 0],        // 20-40 ft: baseline
  [80, 5],        // 40-80 ft: difficult to spot
  [160, 10],      // 80-160 ft: very difficult
  [Infinity, 15], // 160+ ft: nearly impossible
];

const VISIBILITY_HEAVY_COVER: StealthDistanceEntry[] = [
  [10, 0],        // 5-10 ft: baseline
  [20, 5],        // 10-20 ft: difficult
  [40, 10],       // 20-40 ft: very difficult
  [Infinity, 15], // 40+ ft: nearly impossible
];

const VISIBILITY_WATER: StealthDistanceEntry[] = [
  [Infinity, -10], // Very hard to hide on water
];

const VISIBILITY_URBAN: StealthDistanceEntry[] = [
  [20, 0],        // Crowds provide some cover
  [40, 5],
  [80, 10],
  [Infinity, 15],
];

// Terrain type with properties
export interface TerrainType {
  name: TerrainTypeName;
  baseTravelTimeMs: number;  // Time to travel one league in milliseconds
  stealthDistanceTable: StealthDistanceEntry[];
  navigationDifficulty: number;  // How hard it is to get lost (higher = harder to navigate)
  
  /** Get stealth modifier based on distance in feet */
  getStealthModifier(distanceFt: number): number;
}

/** Create a terrain type with the stealth modifier function */
function createTerrainType(
  name: TerrainTypeName,
  baseTravelTimeMs: number,
  stealthDistanceTable: StealthDistanceEntry[],
  navigationDifficulty: number = 0
): TerrainType {
  return {
    name,
    baseTravelTimeMs,
    stealthDistanceTable,
    navigationDifficulty,
    getStealthModifier(distanceFt: number): number {
      for (const [maxDistance, modifier] of this.stealthDistanceTable) {
        if (distanceFt <= maxDistance) {
          return modifier;
        }
      }
      // Beyond all thresholds, return last modifier
      if (this.stealthDistanceTable.length > 0) {
        return this.stealthDistanceTable[this.stealthDistanceTable.length - 1][1];
      }
      return 0;
    }
  };
}

// Registry of terrain types with their properties
export const TERRAIN_TYPES: Record<TerrainTypeName, TerrainType> = {
  // Undefined
  undefined: createTerrainType('undefined', MovementCategory.EASY, VISIBILITY_OPEN, 10),
  
  // Easy Movement + Open Visibility
  open_terrain: createTerrainType('open_terrain', MovementCategory.EASY, VISIBILITY_OPEN, 5),
  road: createTerrainType('road', MovementCategory.EASY, VISIBILITY_OPEN, 0),  // Auto-success
  
  // Moderate Movement + Light Cover
  light_forest: createTerrainType('light_forest', MovementCategory.MODERATE, VISIBILITY_LIGHT_COVER, 10),
  rolling_hills: createTerrainType('rolling_hills', MovementCategory.MODERATE, VISIBILITY_LIGHT_COVER, 10),
  
  // Difficult Movement + Heavy Cover
  heavy_forest: createTerrainType('heavy_forest', MovementCategory.DIFFICULT, VISIBILITY_HEAVY_COVER, 15),
  jungle: createTerrainType('jungle', MovementCategory.DIFFICULT, VISIBILITY_HEAVY_COVER, 20),
  swamp: createTerrainType('swamp', MovementCategory.DIFFICULT, VISIBILITY_HEAVY_COVER, 20),
  
  // Difficult Movement + Light Cover
  mountain: createTerrainType('mountain', MovementCategory.DIFFICULT, VISIBILITY_LIGHT_COVER, 15),
  bog: createTerrainType('bog', MovementCategory.DIFFICULT, VISIBILITY_LIGHT_COVER, 15),
  
  // Extreme Movement + Open Visibility
  alpine: createTerrainType('alpine', MovementCategory.EXTREME, VISIBILITY_OPEN, 10),
  scree: createTerrainType('scree', MovementCategory.EXTREME, VISIBILITY_OPEN, 10),
  
  // Special terrain
  water: createTerrainType('water', MovementCategory.IMPASSABLE, VISIBILITY_WATER, 0),
  urban: createTerrainType('urban', MovementCategory.EASY, VISIBILITY_URBAN, 0),  // Auto-success
};

export function getTerrainType(name: TerrainTypeName): TerrainType {
  return TERRAIN_TYPES[name] ?? TERRAIN_TYPES.undefined;
}

export interface HexCoordinate {
  q: number;
  r: number;
  s: number;
}

/** Validate that q + r + s = 0 */
export function isValidHexCoordinate(coord: HexCoordinate): boolean {
  return coord.q + coord.r + coord.s === 0;
}

/** Create a validated hex coordinate (throws if invalid) */
export function createHexCoordinate(q: number, r: number, s: number): HexCoordinate {
  const coord = { q, r, s };
  if (!isValidHexCoordinate(coord)) {
    throw new Error(`Invalid hex coordinate: q + r + s must equal 0, got ${q + r + s}`);
  }
  return coord;
}

export interface HexCell {
  id: string;
  q: number;
  r: number;
  s: number;
  layer_id: number;
  terrain_type: TerrainTypeName;
  created_at: string;
  updated_at: string;
}

/** Get full terrain properties for a hex cell */
export function getHexCellTerrain(cell: HexCell): TerrainType {
  return getTerrainType(cell.terrain_type);
}

export interface HexCellCreate {
  q: number;
  r: number;
  s: number;
  layer_id?: number;
  terrain_type?: TerrainTypeName;
}
```

---

## Coordinate Conversion Functions

### Pixel (Lat/Lng) to Hex

```typescript
// Constants
const HEX_WIDTH_MILES = 3; // Edge-to-edge distance in miles
const METERS_PER_MILE = 1609.344;
const HEX_WIDTH_METERS = HEX_WIDTH_MILES * METERS_PER_MILE; // ~4828m
const HEX_SIZE = HEX_WIDTH_METERS / Math.sqrt(3); // Circumradius ~2787m

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
  const qFrac = (Math.sqrt(3)/3 * x - 1/3 * y) / HEX_SIZE;
  const rFrac = (2/3 * y) / HEX_SIZE;
  
  return hexRound(qFrac, rFrac);
}

function hexToLatLng(q: number, r: number, s: number): [number, number] {
  // Validate parity
  if (q + r + s !== 0) {
    throw new Error(`Invalid hex coordinate: q + r + s must equal 0, got ${q + r + s}`);
  }
  
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
function hexRound(qFrac: number, rFrac: number): HexCoordinate {
  const sFrac = -qFrac - rFrac;
  
  let q = Math.round(qFrac);
  let r = Math.round(rFrac);
  let s = Math.round(sFrac);
  
  const q_diff = Math.abs(q - qFrac);
  const r_diff = Math.abs(r - rFrac);
  const s_diff = Math.abs(s - sFrac);
  
  // Reset the component with largest rounding error to maintain q + r + s = 0
  if (q_diff > r_diff && q_diff > s_diff) {
    q = -r - s;
  } else if (r_diff > s_diff) {
    r = -q - s;
  } else {
    s = -q - r;
  }
  
  return { q, r, s };
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

# GET /api/hex-cells/{layer_id}/{q}/{r}/{s}
# Returns a specific hex cell (creates with defaults if doesn't exist)
# Validates that q + r + s = 0

# PUT /api/hex-cells/{layer_id}/{q}/{r}/{s}
# Updates a hex cell (terrain_type, etc.)
# Validates that q + r + s = 0

# GET /api/hex-cells/at-location?lat={lat}&lng={lng}&layer_id=0
# Returns the hex cell containing the given coordinates
```

---

## Storage Strategy

### Blob Storage (File-Based)

Each hex cell is stored as an individual JSON file in blob storage:

```
data/hex_cells/
├── layer_0/
│   ├── 0_0_0.json          # Origin (Haden)
│   ├── 1_0_-1.json
│   ├── 1_-1_0.json
│   ├── 0_1_-1.json
│   ├── -1_1_0.json
│   ├── -1_0_1.json
│   ├── 0_-1_1.json
│   └── ...
├── layer_1/                 # Future: underground
│   └── ...
└── layer_2/                 # Future: aerial
    └── ...
```

### File Naming Convention

**Format:** `{q}_{r}_{s}.json`

Examples:
- Origin hex: `0_0_0.json`
- Hex at (1, -1, 0): `1_-1_0.json`
- Hex at (-2, 1, 1): `-2_1_1.json`

### File Content Example

```json
{
  "id": "layer_0_q_0_r_0_s_0",
  "q": 0,
  "r": 0,
  "s": 0,
  "layer_id": 0,
  "terrain_type": "plains",
  "created_at": "2026-02-01T12:00:00Z",
  "updated_at": "2026-02-01T12:00:00Z"
}
```

### Storage Interface

```python
# interfaces/hex_grid.py

from abc import ABC, abstractmethod
from typing import Optional

class IHexGridStorage(ABC):
    @abstractmethod
    def get(self, layer_id: int, q: int, r: int, s: int) -> Optional[HexCell]:
        """Get a hex cell by coordinates, returns None if not found"""
        pass
    
    @abstractmethod
    def get_or_create(self, layer_id: int, q: int, r: int, s: int) -> HexCell:
        """Get a hex cell, creating with defaults if it doesn't exist"""
        pass
    
    @abstractmethod
    def save(self, cell: HexCell) -> HexCell:
        """Save a hex cell to storage"""
        pass
    
    @abstractmethod
    def get_range(
        self, 
        layer_id: int, 
        min_q: int, max_q: int, 
        min_r: int, max_r: int
    ) -> list[HexCell]:
        """Get all hex cells in a coordinate range"""
        pass
    
    @abstractmethod
    def delete(self, layer_id: int, q: int, r: int, s: int) -> bool:
        """Delete a hex cell, returns True if deleted"""
        pass
```

### Provider Implementation

```python
# providers/local_file_hex_grid.py

class LocalFileHexGridStorage(IHexGridStorage):
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
    
    def _get_file_path(self, layer_id: int, q: int, r: int, s: int) -> Path:
        """Generate file path: data/hex_cells/layer_{id}/{q}_{r}_{s}.json"""
        return self.base_path / f"layer_{layer_id}" / f"{q}_{r}_{s}.json"
    
    def get(self, layer_id: int, q: int, r: int, s: int) -> Optional[HexCell]:
        # Validate parity
        if q + r + s != 0:
            raise ValueError(f"Invalid coordinates: q + r + s must equal 0")
        
        file_path = self._get_file_path(layer_id, q, r, s)
        if not file_path.exists():
            return None
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        return HexCell(**data)
    
    # ... other methods
```

### Benefits of This Approach

1. **Simple file naming**: `q_r_s.json` is human-readable and debuggable
2. **Built-in parity validation**: File name encodes all three coordinates
3. **Lazy loading**: Only create files for hexes that have been modified
4. **Easy backup/sync**: Standard file operations work
5. **Layer isolation**: Each layer is a separate directory
6. **Compatible with Azure Blob Storage**: Same pattern works with blob provider

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

This implementation uses **cube coordinates (q, r, s) with pointy-top orientation** centered on Haden (0, 0, 0). The constraint `q + r + s = 0` serves as a parity check for data integrity. Each hex represents a **3-mile (edge-to-edge) area** and includes a terrain type. The layer system (starting with layer 0 for ground) provides future extensibility for underground/aerial regions.
