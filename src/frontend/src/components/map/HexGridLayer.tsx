/**
 * HexGridLayer - Renders a hex grid overlay on a Leaflet map.
 * 
 * Displays pointy-top hexes with cube coordinates (q, r, s).
 * Coordinate labels are shown at the bottom-right of each hex
 * with white fill and black stroke for visibility.
 * 
 * Only hexes within the current viewport are rendered for performance.
 */

import { useEffect, useState, useMemo } from 'react';
import { useMap, Polygon, LayerGroup, Marker } from 'react-leaflet';
import L from 'leaflet';
import type { HexCoordinate } from '../../utils/hexUtils';
import {
  hexToPixel,
  pixelToHex,
  getHexCorners,
  getHexLabel,
  metersToLatLng,
  latLngToMeters,
  HEX_SIZE_M,
} from '../../utils/hexUtils';

interface HexGridLayerProps {
  /** Minimum zoom level to show the grid (default: 10) */
  minZoom?: number;
  /** Minimum zoom level to show coordinate labels (default: 13) */
  showLabelsAtZoom?: number;
  /** Stroke color for hex outlines (default: '#666') */
  strokeColor?: string;
  /** Stroke weight for hex outlines (default: 1) */
  strokeWeight?: number;
}

interface HexRenderData {
  hex: HexCoordinate;
  corners: L.LatLng[];
  labelPosition: L.LatLng;
  label: string;
}

export default function HexGridLayer({
  minZoom = 10,
  showLabelsAtZoom = 10,
  strokeColor = '#666666',
  strokeWeight = 1,
}: HexGridLayerProps) {
  const map = useMap();
  const [zoom, setZoom] = useState(map.getZoom());
  const [bounds, setBounds] = useState(map.getBounds());

  // Update state on map events
  useEffect(() => {
    const handleMoveEnd = () => {
      setBounds(map.getBounds());
    };
    const handleZoomEnd = () => {
      setZoom(map.getZoom());
      setBounds(map.getBounds());
    };

    map.on('moveend', handleMoveEnd);
    map.on('zoomend', handleZoomEnd);

    return () => {
      map.off('moveend', handleMoveEnd);
      map.off('zoomend', handleZoomEnd);
    };
  }, [map]);

  // Calculate visible hexes based on current viewport
  const hexes = useMemo((): HexRenderData[] => {
    if (zoom < minZoom) {
      return [];
    }

    // Convert viewport corners to meter coordinates relative to origin
    const nw = latLngToMeters({ lat: bounds.getNorth(), lng: bounds.getWest() });
    const ne = latLngToMeters({ lat: bounds.getNorth(), lng: bounds.getEast() });
    const sw = latLngToMeters({ lat: bounds.getSouth(), lng: bounds.getWest() });
    const se = latLngToMeters({ lat: bounds.getSouth(), lng: bounds.getEast() });

    // Find meter bounds
    const minX = Math.min(nw.x, ne.x, sw.x, se.x);
    const maxX = Math.max(nw.x, ne.x, sw.x, se.x);
    const minY = Math.min(nw.y, ne.y, sw.y, se.y);
    const maxY = Math.max(nw.y, ne.y, sw.y, se.y);

    // Convert pixel bounds to hex coordinates (with buffer)
    const buffer = HEX_SIZE_M * 2;
    const topLeftHex = pixelToHex(minX - buffer, maxY + buffer);
    const bottomRightHex = pixelToHex(maxX + buffer, minY - buffer);

    // Calculate hex range
    const minQ = Math.min(topLeftHex.q, bottomRightHex.q) - 1;
    const maxQ = Math.max(topLeftHex.q, bottomRightHex.q) + 1;
    const minR = Math.min(topLeftHex.r, bottomRightHex.r) - 1;
    const maxR = Math.max(topLeftHex.r, bottomRightHex.r) + 1;

    const result: HexRenderData[] = [];

    // Generate all hexes in range
    for (let q = minQ; q <= maxQ; q++) {
      for (let r = minR; r <= maxR; r++) {
        const s = -q - r;
        const hex: HexCoordinate = { q, r, s };

        // Get corners in pixel coordinates and convert to LatLng
        const pixelCorners = getHexCorners(hex);
        const corners = pixelCorners.map((corner) => {
          const geo = metersToLatLng(corner);
          return L.latLng(geo.lat, geo.lng);
        });

        // Position label at bottom-right inside the hex
        // Bottom-right is roughly at corner 5 direction but inside
        const center = hexToPixel(hex);
        const labelOffset = {
          x: center.x + HEX_SIZE_M * 0.4,
          y: center.y - HEX_SIZE_M * 0.6,
        };
        const labelGeo = metersToLatLng(labelOffset);
        const labelPosition = L.latLng(labelGeo.lat, labelGeo.lng);

        result.push({
          hex,
          corners,
          labelPosition,
          label: getHexLabel(hex),
        });
      }
    }

    return result;
  }, [zoom, bounds, minZoom]);

  // Don't render if below minimum zoom
  if (zoom < minZoom) {
    return null;
  }

  const showLabels = zoom >= showLabelsAtZoom;

  return (
    <LayerGroup>
      {hexes.map((hexData) => (
        <Polygon
          key={`hex-${hexData.hex.q},${hexData.hex.r},${hexData.hex.s}`}
          positions={hexData.corners}
          pathOptions={{
            stroke: true,
            color: strokeColor,
            weight: strokeWeight,
            fill: false,
          }}
        />
      ))}
      {showLabels && hexes.map((hexData) => (
        <Marker
          key={`label-${hexData.hex.q},${hexData.hex.r},${hexData.hex.s}`}
          position={hexData.labelPosition}
          icon={createLabelIcon(hexData.label)}
          interactive={false}
        />
      ))}
    </LayerGroup>
  );
}

/**
 * Creates a DivIcon for hex coordinate labels.
 * White text with black outline for visibility on any background.
 */
function createLabelIcon(label: string): L.DivIcon {
  return L.divIcon({
    className: 'hex-label',
    html: `<span style="
      font-size: 9px;
      font-family: monospace;
      color: white;
      text-shadow: 
        -1px -1px 0 #000,
        1px -1px 0 #000,
        -1px 1px 0 #000,
        1px 1px 0 #000;
      white-space: nowrap;
      pointer-events: none;
    ">${label}</span>`,
    iconSize: [50, 12],
    iconAnchor: [25, 6],
  });
}
