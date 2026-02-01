/**
 * Tests for distanceUtils
 * Testing behavior: Distance calculations, formatting, and segment generation
 */

import { describe, it, expect } from 'vitest';
import L from 'leaflet';
import {
  calculateHorizontalDistanceMeters,
  calculate3DDistanceMeters,
  calculateSegment,
  calculateAllSegments,
  calculateMeasurementSummary,
  formatDistance,
  formatElevationChange,
  formatSegmentLabel,
  generateWaypointId,
} from '../utils/distanceUtils';
import type { MeasureWaypoint } from '../types/measurement';

describe('distanceUtils', () => {
  describe('calculateHorizontalDistanceMeters', () => {
    it('returns 0 for same point', () => {
      const point = L.latLng(61.238, 7.712);
      expect(calculateHorizontalDistanceMeters(point, point)).toBe(0);
    });

    it('calculates distance between two points', () => {
      const from = L.latLng(61.238, 7.712);
      const to = L.latLng(61.248, 7.712); // ~1.1km north
      const distance = calculateHorizontalDistanceMeters(from, to);
      
      // Should be approximately 1112 meters (0.01 degrees * 111.32km/degree)
      expect(distance).toBeGreaterThan(1000);
      expect(distance).toBeLessThan(1200);
    });
  });

  describe('calculate3DDistanceMeters', () => {
    it('returns null if from elevation is null', () => {
      const from = L.latLng(61.238, 7.712);
      const to = L.latLng(61.248, 7.712);
      expect(calculate3DDistanceMeters(from, to, null, 100)).toBeNull();
    });

    it('returns null if to elevation is null', () => {
      const from = L.latLng(61.238, 7.712);
      const to = L.latLng(61.248, 7.712);
      expect(calculate3DDistanceMeters(from, to, 100, null)).toBeNull();
    });

    it('equals horizontal distance when elevations are the same', () => {
      const from = L.latLng(61.238, 7.712);
      const to = L.latLng(61.248, 7.712);
      const horizontal = calculateHorizontalDistanceMeters(from, to);
      const threeD = calculate3DDistanceMeters(from, to, 100, 100);
      
      expect(threeD).toBeCloseTo(horizontal, 5);
    });

    it('is greater than horizontal when there is elevation change', () => {
      const from = L.latLng(61.238, 7.712);
      const to = L.latLng(61.248, 7.712);
      const horizontal = calculateHorizontalDistanceMeters(from, to);
      const threeD = calculate3DDistanceMeters(from, to, 0, 500); // 500m climb
      
      expect(threeD).toBeGreaterThan(horizontal);
    });

    it('calculates 3D distance using Pythagorean theorem', () => {
      // Use points that are approximately 1000m apart horizontally
      const from = L.latLng(61.238, 7.712);
      const to = L.latLng(61.247, 7.712);
      const horizontal = calculateHorizontalDistanceMeters(from, to);
      
      // With 500m elevation change, 3D distance should be sqrt(h^2 + 500^2)
      const elevationDiff = 500;
      const expected = Math.sqrt(horizontal * horizontal + elevationDiff * elevationDiff);
      const threeD = calculate3DDistanceMeters(from, to, 0, 500);
      
      expect(threeD).toBeCloseTo(expected, 5);
    });
  });

  describe('calculateSegment', () => {
    it('calculates segment data correctly', () => {
      const from: MeasureWaypoint = {
        id: 'wp1',
        position: L.latLng(61.238, 7.712),
        elevation: 100,
        loadingElevation: false,
      };
      const to: MeasureWaypoint = {
        id: 'wp2',
        position: L.latLng(61.248, 7.712),
        elevation: 200,
        loadingElevation: false,
      };
      
      const segment = calculateSegment(from, to, 0, 1);
      
      expect(segment.fromIndex).toBe(0);
      expect(segment.toIndex).toBe(1);
      expect(segment.horizontalDistanceFeet).toBeGreaterThan(3000); // ~1100m in feet
      expect(segment.elevationChangeFeet).toBeCloseTo(100 * 3.28084, 0); // 100m elevation gain
      expect(segment.midpoint.lat).toBeCloseTo(61.243, 2);
    });

    it('returns null elevation change when elevation unavailable', () => {
      const from: MeasureWaypoint = {
        id: 'wp1',
        position: L.latLng(61.238, 7.712),
        elevation: null,
        loadingElevation: false,
      };
      const to: MeasureWaypoint = {
        id: 'wp2',
        position: L.latLng(61.248, 7.712),
        elevation: 200,
        loadingElevation: false,
      };
      
      const segment = calculateSegment(from, to, 0, 1);
      
      expect(segment.elevationChangeFeet).toBeNull();
      expect(segment.distance3DFeet).toBeNull();
    });
  });

  describe('calculateAllSegments', () => {
    it('returns empty array for single waypoint', () => {
      const waypoints: MeasureWaypoint[] = [{
        id: 'wp1',
        position: L.latLng(61.238, 7.712),
        elevation: 100,
        loadingElevation: false,
      }];
      
      expect(calculateAllSegments(waypoints)).toEqual([]);
    });

    it('returns correct number of segments', () => {
      const waypoints: MeasureWaypoint[] = [
        { id: 'wp1', position: L.latLng(61.238, 7.712), elevation: 100, loadingElevation: false },
        { id: 'wp2', position: L.latLng(61.248, 7.712), elevation: 150, loadingElevation: false },
        { id: 'wp3', position: L.latLng(61.258, 7.712), elevation: 200, loadingElevation: false },
      ];
      
      const segments = calculateAllSegments(waypoints);
      expect(segments).toHaveLength(2);
    });
  });

  describe('calculateMeasurementSummary', () => {
    it('returns zeros for empty waypoints', () => {
      const summary = calculateMeasurementSummary([]);
      
      expect(summary.totalHorizontalFeet).toBe(0);
      expect(summary.total3DFeet).toBe(0);
      expect(summary.totalGainFeet).toBe(0);
      expect(summary.totalLossFeet).toBe(0);
      expect(summary.waypointCount).toBe(0);
      expect(summary.segmentCount).toBe(0);
    });

    it('calculates totals correctly', () => {
      const waypoints: MeasureWaypoint[] = [
        { id: 'wp1', position: L.latLng(61.238, 7.712), elevation: 100, loadingElevation: false },
        { id: 'wp2', position: L.latLng(61.248, 7.712), elevation: 200, loadingElevation: false },
        { id: 'wp3', position: L.latLng(61.258, 7.712), elevation: 150, loadingElevation: false },
      ];
      
      const summary = calculateMeasurementSummary(waypoints);
      
      expect(summary.waypointCount).toBe(3);
      expect(summary.segmentCount).toBe(2);
      expect(summary.totalGainFeet).toBeCloseTo(100 * 3.28084, 0); // 100m gain
      expect(summary.totalLossFeet).toBeCloseTo(50 * 3.28084, 0); // 50m loss
    });

    it('returns null for 3D distance when any elevation is missing', () => {
      const waypoints: MeasureWaypoint[] = [
        { id: 'wp1', position: L.latLng(61.238, 7.712), elevation: 100, loadingElevation: false },
        { id: 'wp2', position: L.latLng(61.248, 7.712), elevation: null, loadingElevation: false },
      ];
      
      const summary = calculateMeasurementSummary(waypoints);
      
      expect(summary.total3DFeet).toBeNull();
    });
  });

  describe('formatDistance', () => {
    it('formats feet under 1 mile', () => {
      expect(formatDistance(1234)).toBe('1,234 ft');
    });

    it('formats small distances', () => {
      expect(formatDistance(500)).toBe('500 ft');
    });

    it('formats 1 mile with both feet and miles', () => {
      expect(formatDistance(5280)).toBe('5,280 ft (1.00 mi)');
    });

    it('formats miles with two decimals under 10 miles', () => {
      expect(formatDistance(13200)).toBe('13,200 ft (2.50 mi)'); // 2.5 miles
    });

    it('formats miles with one decimal over 10 miles', () => {
      expect(formatDistance(63360)).toBe('63,360 ft (12.0 mi)'); // 12 miles
    });
  });

  describe('formatElevationChange', () => {
    it('formats positive elevation with plus sign', () => {
      expect(formatElevationChange(500)).toBe('+500 ft');
    });

    it('formats negative elevation with minus sign', () => {
      expect(formatElevationChange(-500)).toBe('-500 ft');
    });

    it('formats zero as positive', () => {
      expect(formatElevationChange(0)).toBe('+0 ft');
    });

    it('formats large numbers with commas', () => {
      expect(formatElevationChange(1500)).toBe('+1,500 ft');
    });
  });

  describe('formatSegmentLabel', () => {
    it('shows distance only when no elevation', () => {
      const segment = {
        fromIndex: 0,
        toIndex: 1,
        horizontalDistanceFeet: 1000,
        distance3DFeet: null,
        elevationChangeFeet: null,
        midpoint: L.latLng(0, 0),
      };
      
      expect(formatSegmentLabel(segment)).toBe('1,000 ft');
    });

    it('shows distance and elevation when available', () => {
      const segment = {
        fromIndex: 0,
        toIndex: 1,
        horizontalDistanceFeet: 1000,
        distance3DFeet: 1100,
        elevationChangeFeet: 200,
        midpoint: L.latLng(0, 0),
      };
      
      expect(formatSegmentLabel(segment)).toBe('1,000 ft\n+200 ft');
    });
  });

  describe('generateWaypointId', () => {
    it('generates unique IDs', () => {
      const ids = new Set<string>();
      for (let i = 0; i < 100; i++) {
        ids.add(generateWaypointId());
      }
      expect(ids.size).toBe(100);
    });

    it('starts with wp- prefix', () => {
      expect(generateWaypointId()).toMatch(/^wp-/);
    });
  });
});
