import { API_BASE_URL } from '../config/api';
import type { MapLocation, MapLocationCreate, MapLocationUpdate } from '../types/mapLocation';

export const mapLocationService = {
  async getAll(mapId?: string): Promise<MapLocation[]> {
    let path = `${API_BASE_URL}/api/map-locations`;
    if (mapId) {
      path += `?map_id=${encodeURIComponent(mapId)}`;
    }

    const response = await fetch(path);
    if (!response.ok) {
      throw new Error(`Failed to fetch locations: ${response.statusText}`);
    }
    return response.json();
  },

  async getById(id: string): Promise<MapLocation> {
    const response = await fetch(`${API_BASE_URL}/api/map-locations/${id}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch location: ${response.statusText}`);
    }
    return response.json();
  },

  async create(data: MapLocationCreate): Promise<MapLocation> {
    const response = await fetch(`${API_BASE_URL}/api/map-locations`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    
    if (!response.ok) {
      throw new Error(`Failed to create location: ${response.statusText}`);
    }
    return response.json();
  },

  async update(id: string, data: MapLocationUpdate): Promise<MapLocation> {
    const response = await fetch(`${API_BASE_URL}/api/map-locations/${id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    
    if (!response.ok) {
      throw new Error(`Failed to update location: ${response.statusText}`);
    }
    return response.json();
  },

  async delete(id: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/api/map-locations/${id}`, {
      method: 'DELETE',
    });
    
    if (!response.ok) {
      throw new Error(`Failed to delete location: ${response.statusText}`);
    }
  },
};
