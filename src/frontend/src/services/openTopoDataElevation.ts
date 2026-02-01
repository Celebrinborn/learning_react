/**
 * OpenTopoData Elevation Provider
 * 
 * Fetches elevation data from OpenTopoData API using EU-DEM 25m dataset.
 * EU-DEM covers European countries including Norway with 25m resolution.
 * 
 * API Documentation: https://www.opentopodata.org/
 */

import { SpanStatusCode } from '@opentelemetry/api';
import { getTracer } from '../telemetry';
import type { ElevationProvider, ElevationResponse } from '../types/elevation';

// OpenTopoData API configuration
const OPENTOPODATA_BASE_URL = 'https://api.opentopodata.org/v1';
const DATASET = 'eudem25m'; // EU-DEM 25m resolution, covers Europe including Norway

class OpenTopoDataElevationProvider implements ElevationProvider {
  /**
   * Fetches elevation for a single point.
   * 
   * @param latitude - Latitude in decimal degrees
   * @param longitude - Longitude in decimal degrees
   * @returns Elevation result with height in meters, or error
   * 
   * @example
   * const result = await provider.getElevation(61.238408, 7.712059);
   * if (result.success) {
   *   console.log(`Elevation: ${result.data.elevation}m`);
   * }
   */
  async getElevation(
    latitude: number,
    longitude: number
  ): Promise<ElevationResponse> {
    const tracer = getTracer();
    
    return tracer.startActiveSpan('elevation.get', async (span) => {
      span.setAttribute('elevation.latitude', latitude);
      span.setAttribute('elevation.longitude', longitude);
      span.setAttribute('elevation.dataset', DATASET);
      span.setAttribute('elevation.provider', 'opentopodata');
      
      try {
        const url = `${OPENTOPODATA_BASE_URL}/${DATASET}?locations=${latitude},${longitude}`;
        
        const response = await fetch(url);
        
        if (!response.ok) {
          span.setAttribute('elevation.error_code', 'API_ERROR');
          span.setStatus({ code: SpanStatusCode.ERROR, message: `API returned status ${response.status}` });
          span.end();
          return {
            success: false as const,
            error: {
              message: `API returned status ${response.status}`,
              code: 'API_ERROR' as const,
            },
          };
        }

        const data = await response.json();

        if (data.status !== 'OK' || !data.results?.[0]) {
          span.setAttribute('elevation.error_code', 'NO_DATA');
          span.setStatus({ code: SpanStatusCode.ERROR, message: data.error || 'No elevation data available' });
          span.end();
          return {
            success: false as const,
            error: {
              message: data.error || 'No elevation data available for this location',
              code: 'NO_DATA' as const,
            },
          };
        }

        const result = data.results[0];
        
        // elevation can be null if outside dataset coverage
        if (result.elevation === null) {
          span.setAttribute('elevation.error_code', 'NO_DATA');
          span.setStatus({ code: SpanStatusCode.ERROR, message: 'Location outside dataset coverage' });
          span.end();
          return {
            success: false as const,
            error: {
              message: 'Location is outside EU-DEM dataset coverage',
              code: 'NO_DATA' as const,
            },
          };
        }

        span.setAttribute('elevation.result_meters', result.elevation);
        span.setStatus({ code: SpanStatusCode.OK });
        span.end();
        
        return {
          success: true as const,
          data: {
            elevation: result.elevation,
            latitude: result.location.lat,
            longitude: result.location.lng,
          },
        };
      } catch (error) {
        span.setAttribute('elevation.error_code', 'NETWORK_ERROR');
        span.setStatus({ code: SpanStatusCode.ERROR, message: error instanceof Error ? error.message : 'Network request failed' });
        span.recordException(error instanceof Error ? error : new Error('Network request failed'));
        span.end();
        
        return {
          success: false as const,
          error: {
            message: error instanceof Error ? error.message : 'Network request failed',
            code: 'NETWORK_ERROR' as const,
          },
        };
      }
    });
  }

  /**
   * Fetches elevation for multiple points in a single request.
   * OpenTopoData allows up to 100 locations per request.
   * 
   * @param points - Array of [latitude, longitude] tuples
   * @returns Array of elevation results (maintains order)
   * 
   * @example
   * const points: [number, number][] = [
   *   [61.238408, 7.712059],
   *   [61.240000, 7.715000],
   * ];
   * const results = await provider.getElevationBatch(points);
   */
  async getElevationBatch(
    points: [number, number][]
  ): Promise<ElevationResponse[]> {
    const tracer = getTracer();
    
    return tracer.startActiveSpan('elevation.getBatch', async (span) => {
      span.setAttribute('elevation.point_count', points.length);
      span.setAttribute('elevation.dataset', DATASET);
      span.setAttribute('elevation.provider', 'opentopodata');
      
      if (points.length === 0) {
        span.setStatus({ code: SpanStatusCode.OK });
        span.end();
        return [];
      }

      // OpenTopoData limit is 100 points per request
      if (points.length > 100) {
        span.setAttribute('elevation.chunked', true);
        span.setAttribute('elevation.chunk_count', Math.ceil(points.length / 100));
        
        // Split into chunks and process
        const chunks: [number, number][][] = [];
        for (let i = 0; i < points.length; i += 100) {
          chunks.push(points.slice(i, i + 100));
        }
        
        const results: ElevationResponse[][] = [];
        for (const chunk of chunks) {
          const chunkResults = await this.getElevationBatch(chunk);
          results.push(chunkResults);
        }
        
        const flatResults = results.flat();
        const successCount = flatResults.filter(r => r.success).length;
        span.setAttribute('elevation.success_count', successCount);
        span.setAttribute('elevation.failure_count', flatResults.length - successCount);
        span.setStatus({ code: SpanStatusCode.OK });
        span.end();
        
        return flatResults;
      }

      try {
        const locations = points.map(([lat, lng]) => `${lat},${lng}`).join('|');
        const url = `${OPENTOPODATA_BASE_URL}/${DATASET}?locations=${locations}`;
        
        const response = await fetch(url);
        
        if (!response.ok) {
          span.setAttribute('elevation.error_code', 'API_ERROR');
          span.setStatus({ code: SpanStatusCode.ERROR, message: `API returned status ${response.status}` });
          span.end();
          
          return points.map(() => ({
            success: false as const,
            error: {
              message: `API returned status ${response.status}`,
              code: 'API_ERROR' as const,
            },
          }));
        }

        const data = await response.json();

        if (data.status !== 'OK' || !data.results) {
          span.setAttribute('elevation.error_code', 'NO_DATA');
          span.setStatus({ code: SpanStatusCode.ERROR, message: data.error || 'No elevation data available' });
          span.end();
          
          return points.map(() => ({
            success: false as const,
            error: {
              message: data.error || 'No elevation data available',
              code: 'NO_DATA' as const,
            },
          }));
        }

        const results = data.results.map((result: { elevation: number | null; location: { lat: number; lng: number } }) => {
          if (result.elevation === null) {
            return {
              success: false as const,
              error: {
                message: 'Location is outside EU-DEM dataset coverage',
                code: 'NO_DATA' as const,
              },
            };
          }

          return {
            success: true as const,
            data: {
              elevation: result.elevation,
              latitude: result.location.lat,
              longitude: result.location.lng,
            },
          };
        });
        
        const successCount = results.filter((r: ElevationResponse) => r.success).length;
        span.setAttribute('elevation.success_count', successCount);
        span.setAttribute('elevation.failure_count', results.length - successCount);
        span.setStatus({ code: SpanStatusCode.OK });
        span.end();
        
        return results;
      } catch (error) {
        span.setAttribute('elevation.error_code', 'NETWORK_ERROR');
        span.setStatus({ code: SpanStatusCode.ERROR, message: error instanceof Error ? error.message : 'Network request failed' });
        span.recordException(error instanceof Error ? error : new Error('Network request failed'));
        span.end();
        
        return points.map(() => ({
          success: false as const,
          error: {
            message: error instanceof Error ? error.message : 'Network request failed',
            code: 'NETWORK_ERROR' as const,
          },
        }));
      }
    });
  }
}

// Export singleton instance
export const elevationProvider: ElevationProvider = new OpenTopoDataElevationProvider();
