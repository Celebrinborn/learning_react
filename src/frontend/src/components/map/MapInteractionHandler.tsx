import { useState } from 'react';
import { useMapEvents, Marker } from 'react-leaflet';
import { Icon, LatLng } from 'leaflet';
import markerIcon from 'leaflet/dist/images/marker-icon.png';
import markerShadow from 'leaflet/dist/images/marker-shadow.png';
import markerRetina from 'leaflet/dist/images/marker-icon-2x.png';

const previewIcon = new Icon({
  iconUrl: markerIcon,
  iconRetinaUrl: markerRetina,
  shadowUrl: markerShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
  className: 'preview-marker'
});

interface MapInteractionHandlerProps {
  addingMode: boolean;
  onLocationSelect: (lat: number, lng: number) => void;
}

export default function MapInteractionHandler({ addingMode, onLocationSelect }: MapInteractionHandlerProps) {
  const [previewPosition, setPreviewPosition] = useState<LatLng | null>(null);

  const map = useMapEvents({
    mousemove: (e) => {
      if (addingMode) {
        setPreviewPosition(e.latlng);
      }
    },
    mouseout: () => {
      if (addingMode) {
        setPreviewPosition(null);
      }
    },
    click: (e) => {
      if (addingMode) {
        const { lat, lng } = e.latlng;
        onLocationSelect(lat, lng);
        setPreviewPosition(null);
      }
    },
  });

  // Apply crosshair cursor when in adding mode
  if (map) {
    const container = map.getContainer();
    if (addingMode) {
      container.style.cursor = 'crosshair';
    } else {
      container.style.cursor = '';
    }
  }

  return (
    <>
      {addingMode && previewPosition && (
        <Marker 
          position={previewPosition} 
          icon={previewIcon}
          opacity={0.6}
        />
      )}
    </>
  );
}
