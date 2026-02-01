/**
 * Tests for hex coordinate utility functions
 * Testing behavior: Pure functions for hex coordinate math
 */

import { describe, it, expect } from 'vitest';
import {
  HexCoordinate,
  isValidHexCoordinate,
  hexToPixel,
  pixelToHex,
  getHexCorners,
  getHexId,
  HEX_SIZE_M,
  ORIGIN_LAT,
  ORIGIN_LNG,
} from '../utils/hexUtils';

describe('hexUtils', () => {
  describe('HexCoordinate validation', () => {
    it('validates that q + r + s = 0 for valid coordinates', () => {
      expect(isValidHexCoordinate({ q: 0, r: 0, s: 0 })).toBe(true);
      expect(isValidHexCoordinate({ q: 1, r: -1, s: 0 })).toBe(true);
      expect(isValidHexCoordinate({ q: 3, r: -2, s: -1 })).toBe(true);
      expect(isValidHexCoordinate({ q: -5, r: 3, s: 2 })).toBe(true);
    });

    it('rejects coordinates where q + r + s !== 0', () => {
      expect(isValidHexCoordinate({ q: 1, r: 1, s: 1 })).toBe(false);
      expect(isValidHexCoordinate({ q: 0, r: 0, s: 1 })).toBe(false);
      expect(isValidHexCoordinate({ q: 2, r: -1, s: 0 })).toBe(false);
    });
  });

  describe('hexToPixel', () => {
    it('returns origin (0, 0) for hex (0, 0, 0)', () => {
      const result = hexToPixel({ q: 0, r: 0, s: 0 });
      expect(result.x).toBeCloseTo(0, 5);
      expect(result.y).toBeCloseTo(0, 5);
    });

    it('calculates correct pixel offset for adjacent hexes', () => {
      // For pointy-top hexes:
      // East neighbor (q+1, r, s-1) should be at x = sqrt(3) * size, y = 0
      const east = hexToPixel({ q: 1, r: 0, s: -1 });
      const expectedX = Math.sqrt(3) * HEX_SIZE_M;
      expect(east.x).toBeCloseTo(expectedX, 1);
      expect(east.y).toBeCloseTo(0, 1);
    });

    it('calculates correct pixel offset for hex at (1, -1, 0) - northeast', () => {
      const northeast = hexToPixel({ q: 1, r: -1, s: 0 });
      // For pointy-top: x = sqrt(3) * (q + r/2), y = 3/2 * r
      const expectedX = Math.sqrt(3) * HEX_SIZE_M * (1 + (-1) / 2);
      const expectedY = (3 / 2) * HEX_SIZE_M * -1;
      expect(northeast.x).toBeCloseTo(expectedX, 1);
      expect(northeast.y).toBeCloseTo(expectedY, 1);
    });
  });

  describe('pixelToHex', () => {
    it('returns (0, 0, 0) for origin pixel', () => {
      const result = pixelToHex(0, 0);
      expect(result.q).toBe(0);
      expect(result.r).toBe(0);
      expect(result.s).toBe(0);
    });

    it('rounds to nearest valid hex coordinate', () => {
      // A point slightly off-center should still round to the correct hex
      const result = pixelToHex(100, 100);
      expect(result.q + result.r + result.s).toBe(0); // Must satisfy parity
    });

    it('is inverse of hexToPixel', () => {
      const original: HexCoordinate = { q: 3, r: -2, s: -1 };
      const pixel = hexToPixel(original);
      const roundTrip = pixelToHex(pixel.x, pixel.y);
      
      expect(roundTrip.q).toBe(original.q);
      expect(roundTrip.r).toBe(original.r);
      expect(roundTrip.s).toBe(original.s);
    });
  });

  describe('getHexCorners', () => {
    it('returns 6 corners for a hex', () => {
      const corners = getHexCorners({ q: 0, r: 0, s: 0 });
      expect(corners).toHaveLength(6);
    });

    it('returns corners at correct distance from center', () => {
      const hex: HexCoordinate = { q: 0, r: 0, s: 0 };
      const center = hexToPixel(hex);
      const corners = getHexCorners(hex);

      // Each corner should be HEX_SIZE_M away from center
      corners.forEach((corner) => {
        const dx = corner.x - center.x;
        const dy = corner.y - center.y;
        const distance = Math.sqrt(dx * dx + dy * dy);
        expect(distance).toBeCloseTo(HEX_SIZE_M, 0);
      });
    });

    it('returns corners in correct order for pointy-top hex', () => {
      const corners = getHexCorners({ q: 0, r: 0, s: 0 });
      
      // For pointy-top, corners at angles: 30°, 90°, 150°, 210°, 270°, 330°
      // In standard math coordinates (y increases upward):
      // Corner 1 (90°) has max positive y offset
      // Corner 4 (270°) has max negative y offset
      const center = hexToPixel({ q: 0, r: 0, s: 0 });
      
      // Corner at 90° should have positive y offset (sin(90°) = 1)
      const topCorner = corners[1];
      expect(topCorner.y).toBeGreaterThan(center.y);
      
      // Corner at 270° should have negative y offset (sin(270°) = -1)
      const bottomCorner = corners[4];
      expect(bottomCorner.y).toBeLessThan(center.y);
    });
  });

  describe('getHexId', () => {
    it('generates correct ID for origin hex', () => {
      expect(getHexId({ q: 0, r: 0, s: 0 })).toBe('hex:l0:q0:r0:s0');
    });

    it('generates correct ID for positive coordinates', () => {
      expect(getHexId({ q: 3, r: 2, s: -5 })).toBe('hex:l0:q3:r2:s-5');
    });

    it('generates correct ID for negative coordinates', () => {
      expect(getHexId({ q: -5, r: 3, s: 2 })).toBe('hex:l0:q-5:r3:s2');
    });

    it('supports custom layer ID', () => {
      expect(getHexId({ q: 1, r: -1, s: 0 }, 1)).toBe('hex:l1:q1:r-1:s0');
    });
  });

  describe('constants', () => {
    it('exports HEX_SIZE_M as approximately 2787 meters', () => {
      expect(HEX_SIZE_M).toBeCloseTo(2787, 0);
    });

    it('exports origin coordinates for Haden', () => {
      expect(ORIGIN_LAT).toBeCloseTo(61.238408, 5);
      expect(ORIGIN_LNG).toBeCloseTo(7.712059, 5);
    });
  });

  describe('long distance accuracy', () => {
    // 100 miles = ~160,934 meters
    // 3 miles per hex = 4828.032 meters center-to-center
    // ~33 hexes to travel 100 miles
    const HEXES_PER_100_MILES = Math.round(160934 / 4828.032);

    it('calculates hex coordinates correctly at 100 miles from origin', () => {
      // Create a hex ~33 hexes east of origin (q=33, r=0, s=-33)
      const farEastHex: HexCoordinate = { q: HEXES_PER_100_MILES, r: 0, s: -HEXES_PER_100_MILES };
      
      // Verify parity constraint still holds
      expect(farEastHex.q + farEastHex.r + farEastHex.s).toBe(0);
      
      // Get pixel position directly (not by chaining neighbors)
      const pixel = hexToPixel(farEastHex);
      
      // Expected x offset: sqrt(3) * size * q for pure east movement
      const expectedX = Math.sqrt(3) * HEX_SIZE_M * HEXES_PER_100_MILES;
      expect(pixel.x).toBeCloseTo(expectedX, 0);
      expect(pixel.y).toBeCloseTo(0, 0); // No vertical offset for pure east
    });

    it('round-trips correctly at 100 miles from origin', () => {
      // Test multiple distant hexes in different directions
      const distantHexes: HexCoordinate[] = [
        { q: HEXES_PER_100_MILES, r: 0, s: -HEXES_PER_100_MILES },           // East
        { q: -HEXES_PER_100_MILES, r: 0, s: HEXES_PER_100_MILES },           // West
        { q: 0, r: -HEXES_PER_100_MILES, s: HEXES_PER_100_MILES },           // North
        { q: 0, r: HEXES_PER_100_MILES, s: -HEXES_PER_100_MILES },           // South
        { q: 20, r: -25, s: 5 },                                              // Diagonal NE
        { q: -15, r: 30, s: -15 },                                            // Diagonal SW
      ];

      for (const original of distantHexes) {
        const pixel = hexToPixel(original);
        const roundTrip = pixelToHex(pixel.x, pixel.y);
        
        expect(roundTrip.q).toBe(original.q);
        expect(roundTrip.r).toBe(original.r);
        expect(roundTrip.s).toBe(original.s);
      }
    });

    it('calculates pixel offset directly from origin without accumulation', () => {
      // This test verifies that hexToPixel computes directly, not by summing neighbor offsets
      // If we calculated by chaining 33 neighbor hops, floating point errors would accumulate
      
      const hex: HexCoordinate = { q: 33, r: -17, s: -16 };
      
      // Calculate pixel directly
      const directPixel = hexToPixel(hex);
      
      // Manually calculate what the position SHOULD be using the hex-to-pixel formula
      // For pointy-top: x = size * sqrt(3) * (q + r/2), y = size * 3/2 * r
      const expectedX = HEX_SIZE_M * Math.sqrt(3) * (hex.q + hex.r / 2);
      const expectedY = HEX_SIZE_M * (3 / 2) * hex.r;
      
      // Should match exactly (within floating point precision)
      expect(directPixel.x).toBeCloseTo(expectedX, 6);
      expect(directPixel.y).toBeCloseTo(expectedY, 6);
    });

    it('maintains consistent hex corners at distant locations', () => {
      // Corners should be exactly HEX_SIZE_M from center, even 100 miles away
      const distantHex: HexCoordinate = { q: 33, r: -10, s: -23 };
      const center = hexToPixel(distantHex);
      const corners = getHexCorners(distantHex);
      
      // All 6 corners must be exactly HEX_SIZE_M from center
      corners.forEach((corner, i) => {
        const dx = corner.x - center.x;
        const dy = corner.y - center.y;
        const distance = Math.sqrt(dx * dx + dy * dy);
        expect(distance).toBeCloseTo(HEX_SIZE_M, 3);
      });
    });
  });
});
