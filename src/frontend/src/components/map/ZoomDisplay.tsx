/**
 * ZoomDisplay - Debug component that shows current map zoom level.
 * Displays in bottom-right corner of the map.
 */

import { useState, useEffect } from 'react';
import { useMap } from 'react-leaflet';

export default function ZoomDisplay() {
  const map = useMap();
  const [zoom, setZoom] = useState(map.getZoom());

  useEffect(() => {
    const handleZoom = () => {
      setZoom(map.getZoom());
    };

    map.on('zoomend', handleZoom);
    return () => {
      map.off('zoomend', handleZoom);
    };
  }, [map]);

  return (
    <div
      style={{
        position: 'absolute',
        bottom: '10px',
        right: '10px',
        color: '#666',
        fontSize: '11px',
        fontFamily: 'monospace',
        zIndex: 1000,
        pointerEvents: 'none',
        textShadow: '0 0 2px white, 0 0 2px white',
      }}
    >
      Zoom: {zoom.toFixed(1)}
    </div>
  );
}
