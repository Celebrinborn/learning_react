import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { elevationProvider } from '../services/openTopoDataElevation';
import { formatElevation } from '../types/elevation';

describe('elevationProvider', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('getElevation', () => {
    it('should return elevation data for a valid location', async () => {
      const mockResponse = {
        status: 'OK',
        results: [
          {
            elevation: 450.5,
            location: { lat: 61.238408, lng: 7.712059 },
          },
        ],
      };

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      const result = await elevationProvider.getElevation(61.238408, 7.712059);

      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.elevation).toBe(450.5);
        expect(result.data.latitude).toBe(61.238408);
        expect(result.data.longitude).toBe(7.712059);
      }
    });

    it('should return error when API returns non-OK status', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
      });

      const result = await elevationProvider.getElevation(61.238408, 7.712059);

      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.code).toBe('API_ERROR');
        expect(result.error.message).toContain('500');
      }
    });

    it('should return NO_DATA error when elevation is null', async () => {
      const mockResponse = {
        status: 'OK',
        results: [
          {
            elevation: null,
            location: { lat: 0, lng: 0 },
          },
        ],
      };

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      const result = await elevationProvider.getElevation(0, 0);

      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.code).toBe('NO_DATA');
      }
    });

    it('should return NETWORK_ERROR on fetch failure', async () => {
      global.fetch = vi.fn().mockRejectedValue(new Error('Network timeout'));

      const result = await elevationProvider.getElevation(61.238408, 7.712059);

      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.code).toBe('NETWORK_ERROR');
        expect(result.error.message).toBe('Network timeout');
      }
    });

    it('should return NO_DATA error when API status is not OK', async () => {
      const mockResponse = {
        status: 'INVALID_REQUEST',
        error: 'Invalid coordinates',
      };

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      const result = await elevationProvider.getElevation(999, 999);

      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.code).toBe('NO_DATA');
      }
    });
  });

  describe('getElevationBatch', () => {
    it('should return empty array for empty input', async () => {
      const result = await elevationProvider.getElevationBatch([]);
      expect(result).toEqual([]);
    });

    it('should return elevation data for multiple points', async () => {
      const mockResponse = {
        status: 'OK',
        results: [
          { elevation: 450, location: { lat: 61.238, lng: 7.712 } },
          { elevation: 500, location: { lat: 61.240, lng: 7.715 } },
        ],
      };

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      const points: [number, number][] = [
        [61.238, 7.712],
        [61.240, 7.715],
      ];
      const results = await elevationProvider.getElevationBatch(points);

      expect(results).toHaveLength(2);
      expect(results[0].success).toBe(true);
      expect(results[1].success).toBe(true);
      if (results[0].success && results[1].success) {
        expect(results[0].data.elevation).toBe(450);
        expect(results[1].data.elevation).toBe(500);
      }
    });

    it('should handle mixed results with some null elevations', async () => {
      const mockResponse = {
        status: 'OK',
        results: [
          { elevation: 450, location: { lat: 61.238, lng: 7.712 } },
          { elevation: null, location: { lat: 0, lng: 0 } },
        ],
      };

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      const points: [number, number][] = [
        [61.238, 7.712],
        [0, 0],
      ];
      const results = await elevationProvider.getElevationBatch(points);

      expect(results[0].success).toBe(true);
      expect(results[1].success).toBe(false);
      if (!results[1].success) {
        expect(results[1].error.code).toBe('NO_DATA');
      }
    });

    it('should chunk requests when more than 100 points', async () => {
      const mockResponse100 = {
        status: 'OK',
        results: Array(100).fill({
          elevation: 100,
          location: { lat: 61.0, lng: 7.0 },
        }),
      };

      const mockResponse50 = {
        status: 'OK',
        results: Array(50).fill({
          elevation: 100,
          location: { lat: 61.0, lng: 7.0 },
        }),
      };

      global.fetch = vi.fn()
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(mockResponse100),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(mockResponse50),
        });

      // Create 150 points (should result in 2 API calls: 100 + 50)
      const points: [number, number][] = Array(150).fill([61.0, 7.0]);
      const results = await elevationProvider.getElevationBatch(points);

      expect(results).toHaveLength(150);
      expect(fetch).toHaveBeenCalledTimes(2);
    });
  });

  describe('formatElevation', () => {
    it('should format elevation in meters by default', () => {
      expect(formatElevation(1234)).toBe('1,234 m');
    });

    it('should format elevation in meters when specified', () => {
      expect(formatElevation(500, 'm')).toBe('500 m');
    });

    it('should convert and format elevation in feet', () => {
      expect(formatElevation(100, 'ft')).toBe('328 ft');
    });

    it('should round to nearest whole number', () => {
      expect(formatElevation(123.7)).toBe('124 m');
      expect(formatElevation(123.2)).toBe('123 m');
    });

    it('should handle negative elevations (below sea level)', () => {
      expect(formatElevation(-50)).toBe('-50 m');
    });
  });
});
