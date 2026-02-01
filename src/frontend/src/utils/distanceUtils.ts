/**
 * Distance Utilities
 * 
 * Functions for calculating distances, elevation changes,
 * and formatting measurements for display.
 * 
 * All distance calculations use the Haversine formula for accuracy
 * on the Earth's surface.
 */

import type { LatLng } from 'leaflet';
import { 
  METERS_TO_FEET, 
  FEET_PER_MILE,
  type MeasureWaypoint,
  type SegmentData,
  type MeasurementSummary,
} from '../types/measurement';
import L from 'leaflet';

/**
 * Calculates the horizontal (2D) distance between two points in meters.
 * Uses Leaflet's built-in Haversine formula implementation.
 */
export function calculateHorizontalDistanceMeters(from: LatLng, to: LatLng): number {
  return from.distanceTo(to);
}

/**
 * Calculates the 3D distance between two points including elevation change.
 * Returns null if either elevation is unavailable.
 * 
 * @param from - Starting position
 * @param to - Ending position  
 * @param fromElevation - Elevation at start in meters
 * @param toElevation - Elevation at end in meters
 * @returns 3D distance in meters, or null if elevation unavailable
 */
export function calculate3DDistanceMeters(
  from: LatLng,
  to: LatLng,
  fromElevation: number | null,
  toElevation: number | null
): number | null {
  if (fromElevation === null || toElevation === null) {
    return null;
  }
  
  const horizontalDistance = calculateHorizontalDistanceMeters(from, to);
  const elevationDifference = toElevation - fromElevation;
  
  // Pythagorean theorem for 3D distance
  return Math.sqrt(
    horizontalDistance * horizontalDistance + 
    elevationDifference * elevationDifference
  );
}

/**
 * Calculates segment data between two waypoints.
 */
export function calculateSegment(
  from: MeasureWaypoint,
  to: MeasureWaypoint,
  fromIndex: number,
  toIndex: number
): SegmentData {
  const horizontalMeters = calculateHorizontalDistanceMeters(from.position, to.position);
  const distance3DMeters = calculate3DDistanceMeters(
    from.position,
    to.position,
    from.elevation,
    to.elevation
  );
  
  const elevationChangeMeters = 
    from.elevation !== null && to.elevation !== null
      ? to.elevation - from.elevation
      : null;
  
  // Calculate midpoint for label placement
  const midLat = (from.position.lat + to.position.lat) / 2;
  const midLng = (from.position.lng + to.position.lng) / 2;
  const midpoint = L.latLng(midLat, midLng);
  
  return {
    fromIndex,
    toIndex,
    horizontalDistanceFeet: horizontalMeters * METERS_TO_FEET,
    distance3DFeet: distance3DMeters !== null ? distance3DMeters * METERS_TO_FEET : null,
    elevationChangeFeet: elevationChangeMeters !== null ? elevationChangeMeters * METERS_TO_FEET : null,
    midpoint,
  };
}

/**
 * Calculates all segments from a list of waypoints.
 */
export function calculateAllSegments(waypoints: MeasureWaypoint[]): SegmentData[] {
  const segments: SegmentData[] = [];
  
  for (let i = 0; i < waypoints.length - 1; i++) {
    segments.push(calculateSegment(waypoints[i], waypoints[i + 1], i, i + 1));
  }
  
  return segments;
}

/**
 * Calculates summary statistics for all waypoints.
 */
export function calculateMeasurementSummary(waypoints: MeasureWaypoint[]): MeasurementSummary {
  const segments = calculateAllSegments(waypoints);
  
  let totalHorizontalFeet = 0;
  let total3DFeet: number | null = 0;
  let totalGainFeet = 0;
  let totalLossFeet = 0;
  
  for (const segment of segments) {
    totalHorizontalFeet += segment.horizontalDistanceFeet;
    
    if (segment.distance3DFeet !== null && total3DFeet !== null) {
      total3DFeet += segment.distance3DFeet;
    } else {
      total3DFeet = null;
    }
    
    if (segment.elevationChangeFeet !== null) {
      if (segment.elevationChangeFeet > 0) {
        totalGainFeet += segment.elevationChangeFeet;
      } else {
        totalLossFeet += Math.abs(segment.elevationChangeFeet);
      }
    }
  }
  
  return {
    totalHorizontalFeet,
    total3DFeet,
    totalGainFeet,
    totalLossFeet,
    waypointCount: waypoints.length,
    segmentCount: segments.length,
  };
}

/**
 * Formats a distance in feet for display.
 * Shows feet, and also miles in parentheses for longer distances.
 * 
 * @param feet - Distance in feet
 * @returns Formatted string like "1,234 ft" or "26,400 ft (5.0 mi)"
 */
export function formatDistance(feet: number): string {
  const feetStr = `${Math.round(feet).toLocaleString()} ft`;
  
  if (feet < FEET_PER_MILE) {
    return feetStr;
  }
  
  const miles = feet / FEET_PER_MILE;
  const milesStr = miles < 10 ? miles.toFixed(2) : miles.toFixed(1);
  return `${feetStr} (${milesStr} mi)`;
}

/**
 * Formats elevation change for display (always in feet).
 * Includes + or - prefix for clarity.
 * 
 * @param feet - Elevation change in feet (positive = up, negative = down)
 * @returns Formatted string like "+234 ft" or "-567 ft"
 */
export function formatElevationChange(feet: number): string {
  const prefix = feet >= 0 ? '+' : '';
  return `${prefix}${Math.round(feet).toLocaleString()} ft`;
}

/**
 * Formats a segment label for display on the map.
 * Shows distance and optionally elevation change.
 */
export function formatSegmentLabel(segment: SegmentData): string {
  const distance = formatDistance(segment.horizontalDistanceFeet);
  
  if (segment.elevationChangeFeet !== null) {
    const elevation = formatElevationChange(segment.elevationChangeFeet);
    return `${distance}\n${elevation}`;
  }
  
  return distance;
}

/**
 * Generates a unique ID for a waypoint.
 */
export function generateWaypointId(): string {
  return `wp-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
}
