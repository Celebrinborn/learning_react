import { LocationType } from './locationType';

export interface MapLocation {
  id: string;
  name: string;
  description: string;
  latitude: number;
  longitude: number;
  map_id: string;
  icon_type: LocationType;
  created_at: string;
  updated_at: string;
}

export interface MapLocationCreate {
  name: string;
  description?: string;
  latitude: number;
  longitude: number;
  map_id?: string;
  icon_type?: LocationType;
}

export interface MapLocationUpdate {
  name?: string;
  description?: string;
  latitude?: number;
  longitude?: number;
  map_id?: string;
  icon_type?: LocationType;
}
