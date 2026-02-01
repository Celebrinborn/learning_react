/**
 * Measurement Types
 * 
 * Types for the map measuring tool that calculates distances
 * and elevation changes between waypoints.
 */

import type { LatLng } from 'leaflet';

/**
 * A waypoint in a measurement path.
 * Contains position and elevation data.
 */
export interface MeasureWaypoint {
  /** Unique identifier for the waypoint */
  id: string;
  /** Geographic position */
  position: LatLng;
  /** Elevation in meters (null if not yet loaded or unavailable) */
  elevation: number | null;
  /** Whether elevation is currently being fetched */
  loadingElevation: boolean;
}

/**
 * Distance data for a single segment between two waypoints.
 */
export interface SegmentData {
  /** Index of the starting waypoint */
  fromIndex: number;
  /** Index of the ending waypoint */
  toIndex: number;
  /** Horizontal distance in feet */
  horizontalDistanceFeet: number;
  /** 3D distance including elevation change, in feet (null if elevation unavailable) */
  distance3DFeet: number | null;
  /** Elevation change in feet (positive = uphill, negative = downhill) */
  elevationChangeFeet: number | null;
  /** Midpoint position for label placement */
  midpoint: LatLng;
}

/**
 * Summary of all measurements for the entire path.
 */
export interface MeasurementSummary {
  /** Total horizontal distance in feet */
  totalHorizontalFeet: number;
  /** Total 3D distance in feet (null if any elevation unavailable) */
  total3DFeet: number | null;
  /** Total elevation gain in feet */
  totalGainFeet: number;
  /** Total elevation loss in feet (positive value) */
  totalLossFeet: number;
  /** Number of waypoints */
  waypointCount: number;
  /** Number of segments */
  segmentCount: number;
}

/** Maximum number of waypoints allowed */
export const MAX_WAYPOINTS = 420;

/** Meters to feet conversion factor */
export const METERS_TO_FEET = 3.28084;

/** Feet per mile */
export const FEET_PER_MILE = 5280;
