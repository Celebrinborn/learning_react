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
import { useMap, Polygon, LayerGroup } from 'react-leaflet';
import L from 'leaflet';
import type { HexCoordinate } from '../../utils/hexUtils';
import {
  hexToPixel,
  pixelToHex,
  getHexCorners,
  getHexLabel,
  ORIGIN_LAT,
  ORIGIN_LNG,
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

/**
 * Converts a pixel point (relative to origin) to LatLng using the map's projection.
 */
function pixelToLatLng(map: L.Map, originProjected: L.Point, point: { x: number; y: number }): L.LatLng {
  // Add offset to origin projected point
  // Note: In Leaflet's projected space, y increases downward, but our hex math uses
  // standard math coordinates where y increases upward. We need to invert y.
  const projected = L.point(
    originProjected.x + point.x,
    originProjected.y - point.y  // Invert y for Leaflet's coordinate system
  );
  return map.unproject(projected, map.getZoom());
}

/**
 * Converts a LatLng to pixel point relative to origin.
 */
function latLngToPixel(map: L.Map, originProjected: L.Point, latlng: L.LatLng): { x: number; y: number } {
  const projected = map.project(latlng, map.getZoom());
  return {
    x: projected.x - originProjected.x,
    y: -(projected.y - originProjected.y),  // Invert y back to math coordinates
  };
}

export default function HexGridLayer({
  minZoom = 10,
  showLabelsAtZoom = 13,
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

    const origin = L.latLng(ORIGIN_LAT, ORIGIN_LNG);
    const originProjected = map.project(origin, zoom);

    // Convert viewport corners to pixel coordinates relative to origin
    const nw = latLngToPixel(map, originProjected, L.latLng(bounds.getNorth(), bounds.getWest()));
    const ne = latLngToPixel(map, originProjected, L.latLng(bounds.getNorth(), bounds.getEast()));
    const sw = latLngToPixel(map, originProjected, L.latLng(bounds.getSouth(), bounds.getWest()));
    const se = latLngToPixel(map, originProjected, L.latLng(bounds.getSouth(), bounds.getEast()));

    // Find pixel bounds
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
        const corners = pixelCorners.map((corner) =>
          pixelToLatLng(map, originProjected, corner)
        );

        // Position label at bottom-right inside the hex
        // Bottom-right is roughly at corner 5 direction but inside
        const center = hexToPixel(hex);
        const labelOffset = {
          x: center.x + HEX_SIZE_M * 0.4,
          y: center.y - HEX_SIZE_M * 0.6,
        };
        const labelPosition = pixelToLatLng(map, originProjected, labelOffset);

        result.push({
          hex,
          corners,
          labelPosition,
          label: getHexLabel(hex),
        });
      }
    }

    return result;
  }, [map, zoom, bounds, minZoom]);

  // Don't render if below minimum zoom
  if (zoom < minZoom) {
    return null;
  }

  const showLabels = zoom >= showLabelsAtZoom;

  return (
    <LayerGroup>
      {hexes.map((hexData) => (
        <Polygon
          key={`${hexData.hex.q},${hexData.hex.r},${hexData.hex.s}`}
          positions={hexData.corners}
          pathOptions={{
            stroke: true,
            color: strokeColor,
            weight: strokeWeight,
            fill: false,
          }}
        >
          {showLabels && (
            <HexLabel position={hexData.labelPosition} label={hexData.label} />
          )}
        </Polygon>
      ))}
    </LayerGroup>
  );
}

/**
 * SVG-based label component for hex coordinates.
 * Renders white text with black outline for visibility on any background.
 */
interface HexLabelProps {
  position: L.LatLng;
  label: string;
}

function HexLabel({ position, label }: HexLabelProps) {
  const map = useMap();
  
  // Convert position to pixel coordinates for the SVG overlay
  const point = map.latLngToContainerPoint(position);
  
  return (
    <div
      style={{
        position: 'absolute',
        left: point.x,
        top: point.y,
        transform: 'translate(-50%, -50%)',
        pointerEvents: 'none',
        whiteSpace: 'nowrap',
      }}
    >
      <svg width="60" height="16" style={{ overflow: 'visible' }}>
        <text
          x="30"
          y="12"
          textAnchor="middle"
          style={{
            fontSize: '10px',
            fontFamily: 'monospace',
            fill: 'white',
            stroke: 'black',
            strokeWidth: '2px',
            paintOrder: 'stroke fill',
          }}
        >
          {label}
        </text>
      </svg>
    </div>
  );
}
