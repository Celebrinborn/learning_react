import { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, LayersControl } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { Icon } from 'leaflet';
import { Button, Spinner } from '@fluentui/react-components';
import { Add24Regular, Dismiss24Regular } from '@fluentui/react-icons';

// Fix for default marker icon in React Leaflet
import markerIcon from 'leaflet/dist/images/marker-icon.png';
import markerShadow from 'leaflet/dist/images/marker-shadow.png';
import markerRetina from 'leaflet/dist/images/marker-icon-2x.png';

import { mapLocationService } from '../services/mapLocationService';
import type { MapLocation, MapLocationCreate, MapLocationUpdate } from '../types/mapLocation';
import MapInteractionHandler from '../components/map/MapInteractionHandler';
import LocationModal from '../components/map/LocationModal';
import { LocationTypeIcons } from '../types/locationType';
import L from 'leaflet';

const defaultIcon = new Icon({
  iconUrl: markerIcon,
  iconRetinaUrl: markerRetina,
  shadowUrl: markerShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

// Create custom icon with emoji
const createCustomIcon = (emoji: string) => {
  return L.divIcon({
    html: `<div style="font-size: 24px; text-align: center; line-height: 1;">${emoji}</div>`,
    className: 'custom-marker-icon',
    iconSize: [30, 30],
    iconAnchor: [15, 15],
    popupAnchor: [0, -15],
  });
};

export default function Map() {
  // Årdalsfjord, Vestland county, Norway
  const position: [number, number] = [61.23, 7.70];

  const [locations, setLocations] = useState<MapLocation[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedCoords, setSelectedCoords] = useState<[number, number] | null>(null);
  const [editingLocation, setEditingLocation] = useState<MapLocation | null>(null);
  const [addingMode, setAddingMode] = useState(false);

  // Load locations on mount
  useEffect(() => {
    loadLocations();
  }, []);

  const loadLocations = async () => {
    try {
      setLoading(true);
      const data = await mapLocationService.getAll();
      setLocations(data);
    } catch (error) {
      console.error('Error loading locations:', error);
      alert(`Failed to load locations: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setLoading(false);
    }
  };

  const handleLocationSelect = (lat: number, lng: number) => {
    setSelectedCoords([lat, lng]);
    setEditingLocation(null);
    setModalOpen(true);
    setAddingMode(false);
  };

  const handleToggleAddMode = () => {
    setAddingMode(!addingMode);
  };

  const handleEditLocation = (location: MapLocation) => {
    setEditingLocation(location);
    setSelectedCoords(null);
    setModalOpen(true);
  };

  const handleDeleteLocation = async (location: MapLocation) => {
    if (!window.confirm(`Are you sure you want to delete "${location.name}"?`)) {
      return;
    }

    try {
      await mapLocationService.delete(location.id);
      await loadLocations();
    } catch (error) {
      console.error('Error deleting location:', error);
      alert(`Failed to delete location: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  };

  const handleSaveLocation = async (data: MapLocationCreate | MapLocationUpdate) => {
    if (editingLocation) {
      await mapLocationService.update(editingLocation.id, data as MapLocationUpdate);
    } else {
      await mapLocationService.create(data as MapLocationCreate);
    }
    await loadLocations();
  };

  return (
    <div style={{ height: '100%', width: '100%', position: 'relative' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1>Campaign Map</h1>
        
        {loading && (
          <div style={{ display: 'flex', justifyContent: 'center', padding: '20px' }}>
            <Spinner label="Loading locations..." />
          </div>
        )}
      </div>

      {/* Side Panel with Tools */}
      <div style={{ 
        position: 'absolute', 
        top: '80px', 
        left: '20px', 
        zIndex: 1000,
        display: 'flex',
        flexDirection: 'column',
        gap: '8px',
        backgroundColor: 'white',
        padding: '8px',
        borderRadius: '8px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.15)'
      }}>
        <Button
          appearance={addingMode ? 'primary' : 'secondary'}
          icon={addingMode ? <Dismiss24Regular /> : <Add24Regular />}
          onClick={handleToggleAddMode}
          title={addingMode ? 'Cancel adding' : 'Add interest point'}
        >
          {addingMode ? 'Cancel' : 'Add Point'}
        </Button>
      </div>

      <div style={{ height: 'calc(100vh - 150px)', width: '100%' }}>
        <MapContainer
          center={position}
          zoom={13}
          style={{ height: '100%', width: '100%' }}
        >
          <LayersControl position="topright">
            <LayersControl.BaseLayer checked name="Topographical Map">
              <TileLayer
                attribution='Map data: &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, <a href="http://viewfinderpanoramas.org">SRTM</a> | Map style: &copy; <a href="https://opentopomap.org">OpenTopoMap</a>'
                url="https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png"
                maxZoom={17}
              />
            </LayersControl.BaseLayer>
            
            <LayersControl.BaseLayer name="Standard Map">
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
            </LayersControl.BaseLayer>

            <LayersControl.Overlay name="Land Cover (Biomes)">
              <TileLayer
                attribution='ESRI World Land Cover'
                url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
                opacity={0.5}
              />
            </LayersControl.Overlay>
          </LayersControl>

          <MapInteractionHandler 
            addingMode={addingMode}
            onLocationSelect={handleLocationSelect}
          />

          {locations.map((location) => {
            const icon = location.icon_type && LocationTypeIcons[location.icon_type]
              ? createCustomIcon(LocationTypeIcons[location.icon_type])
              : defaultIcon;
            
            return (
              <Marker
                key={location.id}
                position={[location.latitude, location.longitude]}
                icon={icon}
              >
                <Popup>
                  <div style={{ minWidth: '200px' }}>
                    <h3 style={{ margin: '0 0 8px 0' }}>{location.name}</h3>
                    {location.description && (
                      <p style={{ margin: '0 0 12px 0', fontSize: '14px' }}>{location.description}</p>
                    )}
                    <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
                      <Button
                        size="small"
                        appearance="secondary"
                        onClick={() => handleEditLocation(location)}
                      >
                        Edit
                      </Button>
                      <Button
                        size="small"
                        appearance="secondary"
                        onClick={() => handleDeleteLocation(location)}
                      >
                        Delete
                      </Button>
                    </div>
                  </div>
                </Popup>
              </Marker>
            );
          })}
        </MapContainer>
      </div>

      <LocationModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onSave={handleSaveLocation}
        initialCoords={selectedCoords || undefined}
        editingLocation={editingLocation || undefined}
      />
    </div>
  );
}
