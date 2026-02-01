/**
 * Hex coordinate utilities for cube coordinate system.
 * 
 * Based on Red Blob Games' hexagonal grids guide.
 * Uses pointy-top hexes with 3-mile (4828.032m) center-to-center spacing.
 * 
 * All calculations are performed directly from origin (0,0,0) to avoid
 * accumulating floating point errors from chained neighbor calculations.
 */

// ============================================================================
// Constants
// ============================================================================

/** Center-to-center distance in meters (3 miles) */
export const HEX_CENTER_SPACING_M = 4828.032;

/** Hex circumradius (size) in meters: center_spacing / sqrt(3) */
export const HEX_SIZE_M = HEX_CENTER_SPACING_M / Math.sqrt(3);

/** Origin latitude (Haden) */
export const ORIGIN_LAT = 61.238408;

/** Origin longitude (Haden) */
export const ORIGIN_LNG = 7.712059;

// ============================================================================
// Types
// ============================================================================

/** Cube coordinate for a hex cell */
export interface HexCoordinate {
  q: number;
  r: number;
  s: number;
}

/** 2D point in projected space (meters from origin) */
export interface Point {
  x: number;
  y: number;
}

// ============================================================================
// Validation
// ============================================================================

/**
 * Validates that a hex coordinate satisfies the cube constraint q + r + s = 0
 */
export function isValidHexCoordinate(hex: HexCoordinate): boolean {
  return hex.q + hex.r + hex.s === 0;
}

// ============================================================================
// Coordinate Conversion
// ============================================================================

/**
 * Converts hex cube coordinates to pixel offset from origin.
 * 
 * For pointy-top hexes:
 *   x = size * sqrt(3) * (q + r/2)
 *   y = size * 3/2 * r
 * 
 * This calculates directly from origin, not by chaining neighbor offsets,
 * ensuring consistent precision at any distance.
 */
export function hexToPixel(hex: HexCoordinate): Point {
  const x = HEX_SIZE_M * Math.sqrt(3) * (hex.q + hex.r / 2);
  const y = HEX_SIZE_M * (3 / 2) * hex.r;
  return { x, y };
}

/**
 * Converts pixel offset from origin to hex cube coordinates.
 * 
 * Uses the inverse of hexToPixel formula, then rounds to nearest valid hex.
 */
export function pixelToHex(x: number, y: number): HexCoordinate {
  // Inverse of hexToPixel for pointy-top
  const q = (Math.sqrt(3) / 3 * x - 1 / 3 * y) / HEX_SIZE_M;
  const r = (2 / 3 * y) / HEX_SIZE_M;
  
  return hexRound(q, r);
}

/**
 * Rounds fractional hex coordinates to the nearest valid integer hex.
 * 
 * Ensures the cube constraint q + r + s = 0 is maintained by
 * adjusting the component with the largest rounding error.
 */
function hexRound(qFrac: number, rFrac: number): HexCoordinate {
  const sFrac = -qFrac - rFrac;
  
  let q = Math.round(qFrac);
  let r = Math.round(rFrac);
  let s = Math.round(sFrac);
  
  const qDiff = Math.abs(q - qFrac);
  const rDiff = Math.abs(r - rFrac);
  const sDiff = Math.abs(s - sFrac);
  
  // Reset the component with largest rounding error to maintain parity
  if (qDiff > rDiff && qDiff > sDiff) {
    q = -r - s;
  } else if (rDiff > sDiff) {
    r = -q - s;
  } else {
    s = -q - r;
  }
  
  // Convert -0 to 0 to avoid Object.is comparison issues
  return {
    q: q === 0 ? 0 : q,
    r: r === 0 ? 0 : r,
    s: s === 0 ? 0 : s,
  };
}

// ============================================================================
// Hex Geometry
// ============================================================================

/**
 * Returns the 6 corner points of a hex in pixel coordinates.
 * 
 * For pointy-top hexes, corners start at 30° and go counterclockwise:
 *   Corner 0: 30° (upper-right)
 *   Corner 1: 90° (top)
 *   Corner 2: 150° (upper-left)
 *   Corner 3: 210° (lower-left)
 *   Corner 4: 270° (bottom)
 *   Corner 5: 330° (lower-right)
 */
export function getHexCorners(hex: HexCoordinate): Point[] {
  const center = hexToPixel(hex);
  const corners: Point[] = [];
  
  for (let i = 0; i < 6; i++) {
    // Pointy-top: first corner at 30°, then every 60°
    const angleDeg = 60 * i + 30;
    const angleRad = (Math.PI / 180) * angleDeg;
    
    corners.push({
      x: center.x + HEX_SIZE_M * Math.cos(angleRad),
      y: center.y + HEX_SIZE_M * Math.sin(angleRad),
    });
  }
  
  return corners;
}

// ============================================================================
// Hex ID Generation
// ============================================================================

/**
 * Generates a canonical, stable hex ID string.
 * 
 * Format: hex:l{layer}:q{q}:r{r}:s{s}
 * 
 * Examples:
 *   - Origin: hex:l0:q0:r0:s0
 *   - (3, -2, -1) layer 0: hex:l0:q3:r-2:s-1
 */
export function getHexId(hex: HexCoordinate, layerId: number = 0): string {
  return `hex:l${layerId}:q${hex.q}:r${hex.r}:s${hex.s}`;
}

/**
 * Formats hex coordinates as a display label.
 * 
 * Format: "q, r, s"
 */
export function getHexLabel(hex: HexCoordinate): string {
  return `${hex.q}, ${hex.r}, ${hex.s}`;
}
