/**
 * MeasureTool - Google Maps style measuring tool for the map.
 * 
 * Allows users to click to add waypoints and measure distances
 * with elevation changes displayed. Waypoints are draggable.
 * 
 * Features:
 * - Click to add waypoints (up to 420)
 * - Drag waypoints to adjust path
 * - Shows segment distances and elevation changes
 * - Summary panel with totals
 */

import { useState, useEffect, useCallback, useMemo } from 'react';
import { useMapEvents, Polyline, Marker, Tooltip } from 'react-leaflet';
import L from 'leaflet';
import type { MeasureWaypoint, MeasurementSummary } from '../../types/measurement';
import { MAX_WAYPOINTS, METERS_TO_FEET } from '../../types/measurement';
import {
  calculateAllSegments,
  calculateMeasurementSummary,
  formatDistance,
  formatSegmentLabel,
  generateWaypointId,
} from '../../utils/distanceUtils';
import { elevationProvider } from '../../services/openTopoDataElevation';

interface MeasureToolProps {
  /** Whether the tool is active */
  active: boolean;
  /** Callback when tool is closed/deactivated */
  onClose: () => void;
}

// Create waypoint marker icons - small grey dots like Google Earth
function createWaypointIcon(): L.DivIcon {
  return L.divIcon({
    className: 'measure-waypoint',
    html: `<div style="
      width: 10px;
      height: 10px;
      background: white;
      border: 2px solid #555;
      border-radius: 50%;
      box-shadow: 0 1px 3px rgba(0,0,0,0.4);
      cursor: move;
    "></div>`,
    iconSize: [10, 10],
    iconAnchor: [5, 5],
  });
}

// Create segment label icon - black text with white outline
function createSegmentLabelIcon(text: string): L.DivIcon {
  const lines = text.split('\n');
  const html = lines.map(line => `<div>${line}</div>`).join('');
  
  return L.divIcon({
    className: 'measure-segment-label',
    html: `<div style="
      font-size: 12px;
      font-family: system-ui, sans-serif;
      font-weight: 600;
      white-space: nowrap;
      text-align: center;
      line-height: 1.4;
      color: #000;
      text-shadow: 
        -1px -1px 0 #fff,
        1px -1px 0 #fff,
        -1px 1px 0 #fff,
        1px 1px 0 #fff,
        0 -1px 0 #fff,
        0 1px 0 #fff,
        -1px 0 0 #fff,
        1px 0 0 #fff;
      transform: translate(-50%, -50%);
    ">${html}</div>`,
  });
}

export default function MeasureTool({ active, onClose }: MeasureToolProps) {
  const [waypoints, setWaypoints] = useState<MeasureWaypoint[]>([]);
  
  // Clear waypoints when tool is deactivated
  useEffect(() => {
    if (!active) {
      setWaypoints([]);
    }
  }, [active]);
  
  // Fetch elevation for a waypoint
  const fetchElevation = useCallback(async (waypointId: string, lat: number, lng: number) => {
    try {
      const result = await elevationProvider.getElevation(lat, lng);
      
      setWaypoints(prev => prev.map(wp => {
        if (wp.id === waypointId) {
          return {
            ...wp,
            elevation: result.success ? result.data.elevation : null,
            loadingElevation: false,
          };
        }
        return wp;
      }));
    } catch {
      setWaypoints(prev => prev.map(wp => {
        if (wp.id === waypointId) {
          return { ...wp, elevation: null, loadingElevation: false };
        }
        return wp;
      }));
    }
  }, []);
  
  // Handle map click to add waypoint
  useMapEvents({
    click: (e) => {
      if (!active) return;
      if (waypoints.length >= MAX_WAYPOINTS) return;
      
      const newWaypoint: MeasureWaypoint = {
        id: generateWaypointId(),
        position: e.latlng,
        elevation: null,
        loadingElevation: true,
      };
      
      setWaypoints(prev => [...prev, newWaypoint]);
      fetchElevation(newWaypoint.id, e.latlng.lat, e.latlng.lng);
    },
  });
  
  // Handle waypoint drag
  const handleWaypointDrag = useCallback((waypointId: string, newPosition: L.LatLng) => {
    setWaypoints(prev => prev.map(wp => {
      if (wp.id === waypointId) {
        return {
          ...wp,
          position: newPosition,
          elevation: null,
          loadingElevation: true,
        };
      }
      return wp;
    }));
    
    // Fetch new elevation for dragged position
    fetchElevation(waypointId, newPosition.lat, newPosition.lng);
  }, [fetchElevation]);
  
  // Handle double-click to remove waypoint
  const handleWaypointRemove = useCallback((waypointId: string) => {
    setWaypoints(prev => prev.filter(wp => wp.id !== waypointId));
  }, []);
  
  // Calculate segments and summary
  const segments = useMemo(() => calculateAllSegments(waypoints), [waypoints]);
  const summary = useMemo(() => calculateMeasurementSummary(waypoints), [waypoints]);
  
  // Generate polyline positions
  const polylinePositions = useMemo(() => 
    waypoints.map(wp => wp.position),
    [waypoints]
  );
  
  if (!active) return null;
  
  return (
    <>
      {/* Measurement path polyline */}
      {waypoints.length >= 2 && (
        <Polyline
          positions={polylinePositions}
          pathOptions={{
            color: '#3b82f6',
            weight: 3,
            opacity: 0.8,
            dashArray: '10, 5',
          }}
        />
      )}
      
      {/* Segment distance labels */}
      {segments.map((segment, index) => (
        <Marker
          key={`segment-${index}`}
          position={segment.midpoint}
          icon={createSegmentLabelIcon(formatSegmentLabel(segment))}
          interactive={false}
        />
      ))}
      
      {/* Waypoint markers */}
      {waypoints.map((waypoint) => (
        <Marker
          key={waypoint.id}
          position={waypoint.position}
          icon={createWaypointIcon()}
          draggable={true}
          eventHandlers={{
            dragend: (e) => {
              const marker = e.target as L.Marker;
              handleWaypointDrag(waypoint.id, marker.getLatLng());
            },
            dblclick: (e) => {
              L.DomEvent.stopPropagation(e);
              handleWaypointRemove(waypoint.id);
            },
          }}
        >
          <Tooltip direction="top" offset={[0, -15]} opacity={0.9}>
            <div style={{ textAlign: 'center' }}>
              {waypoint.loadingElevation ? (
                <span>Loading elevation...</span>
              ) : waypoint.elevation !== null ? (
                <span>Elevation: {Math.round(waypoint.elevation * METERS_TO_FEET).toLocaleString()} ft</span>
              ) : (
                <span>Elevation: N/A</span>
              )}
              <br />
              <small style={{ opacity: 0.7 }}>Double-click to remove</small>
            </div>
          </Tooltip>
        </Marker>
      ))}
      
      {/* Summary panel */}
      <MeasureSummaryPanel 
        summary={summary} 
        onClose={onClose}
      />
    </>
  );
}

interface MeasureSummaryPanelProps {
  summary: MeasurementSummary;
  onClose: () => void;
}

function MeasureSummaryPanel({ summary, onClose }: MeasureSummaryPanelProps) {
  if (summary.waypointCount === 0) {
    return (
      <div style={{
        position: 'absolute',
        bottom: '20px',
        left: '50%',
        transform: 'translateX(-50%)',
        background: 'rgba(255, 255, 255, 0.95)',
        padding: '6px 12px',
        borderRadius: '4px',
        boxShadow: '0 1px 4px rgba(0,0,0,0.2)',
        zIndex: 1000,
        fontFamily: 'system-ui, sans-serif',
        fontSize: '12px',
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
      }}>
        <span style={{ color: '#666' }}>Click to measure</span>
        <button
          onClick={onClose}
          style={{
            padding: '2px 8px',
            border: '1px solid #ccc',
            borderRadius: '3px',
            background: 'white',
            cursor: 'pointer',
            fontSize: '11px',
          }}
        >
          Cancel
        </button>
      </div>
    );
  }
  
  return (
    <div style={{
      position: 'absolute',
      bottom: '20px',
      left: '50%',
      transform: 'translateX(-50%)',
      background: 'rgba(255, 255, 255, 0.95)',
      padding: '6px 12px',
      borderRadius: '4px',
      boxShadow: '0 1px 4px rgba(0,0,0,0.2)',
      zIndex: 1000,
      fontFamily: 'system-ui, sans-serif',
      fontSize: '12px',
      display: 'flex',
      alignItems: 'center',
      gap: '12px',
      whiteSpace: 'nowrap',
    }}>
      <span><strong>{formatDistance(summary.totalHorizontalFeet)}</strong></span>
      <span style={{ color: '#22c55e' }}>↑{Math.round(summary.totalGainFeet).toLocaleString()}</span>
      <span style={{ color: '#ef4444' }}>↓{Math.round(summary.totalLossFeet).toLocaleString()}</span>
      <button
        onClick={onClose}
        style={{
          padding: '2px 8px',
          border: '1px solid #ccc',
          borderRadius: '3px',
          background: 'white',
          cursor: 'pointer',
          fontSize: '11px',
        }}
      >
        Done
      </button>
    </div>
  );
}
