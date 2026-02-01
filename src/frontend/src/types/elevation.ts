/**
 * Elevation Provider Interface
 * 
 * Defines the contract for elevation data providers.
 * Implementations can use different APIs (OpenTopoData, Mapbox, etc.)
 */

export interface ElevationResult {
  elevation: number; // meters above sea level
  latitude: number;
  longitude: number;
}

export interface ElevationError {
  message: string;
  code: 'NETWORK_ERROR' | 'API_ERROR' | 'NO_DATA';
}

export type ElevationResponse = 
  | { success: true; data: ElevationResult }
  | { success: false; error: ElevationError };

/**
 * Interface for elevation data providers.
 * All elevation providers must implement this contract.
 */
export interface ElevationProvider {
  /**
   * Fetches elevation for a single point.
   * 
   * @param latitude - Latitude in decimal degrees
   * @param longitude - Longitude in decimal degrees
   * @returns Elevation result with height in meters, or error
   */
  getElevation(latitude: number, longitude: number): Promise<ElevationResponse>;

  /**
   * Fetches elevation for multiple points.
   * 
   * @param points - Array of [latitude, longitude] tuples
   * @returns Array of elevation results (maintains order)
   */
  getElevationBatch(points: [number, number][]): Promise<ElevationResponse[]>;
}

/**
 * Formats elevation for display.
 * 
 * @param meters - Elevation in meters
 * @param unit - Display unit ('m' for meters, 'ft' for feet)
 * @returns Formatted string like "1,234 m" or "4,049 ft"
 */
export function formatElevation(
  meters: number,
  unit: 'm' | 'ft' = 'm'
): string {
  if (unit === 'ft') {
    const feet = meters * 3.28084;
    return `${Math.round(feet).toLocaleString()} ft`;
  }
  return `${Math.round(meters).toLocaleString()} m`;
}
