/**
 * Tests for HexGridLayer component
 * Testing behavior: Renders hex grid overlay with coordinate labels
 */

import { describe, it, expect, vi } from 'vitest';
import { render } from '@testing-library/react';
import HexGridLayer from '../components/map/HexGridLayer';

// Mock react-leaflet hooks and components
const mockMap = {
  getZoom: vi.fn(() => 13),
  getBounds: vi.fn(() => ({
    getNorth: () => 61.25,
    getSouth: () => 61.22,
    getEast: () => 7.75,
    getWest: () => 7.68,
  })),
  project: vi.fn((latlng: { lat: number; lng: number }) => ({
    x: (latlng.lng - 7.712059) * 100000,
    y: (61.238408 - latlng.lat) * 100000,
  })),
  unproject: vi.fn((point: { x: number; y: number }) => ({
    lat: 61.238408 - point.y / 100000,
    lng: 7.712059 + point.x / 100000,
  })),
  latLngToContainerPoint: vi.fn(() => ({ x: 100, y: 100 })),
  on: vi.fn(),
  off: vi.fn(),
};

vi.mock('react-leaflet', () => ({
  useMap: vi.fn(() => mockMap),
  Polygon: vi.fn(({ children, positions, pathOptions }: { children?: React.ReactNode; positions: unknown; pathOptions: unknown }) => (
    <div data-testid="hex-polygon" data-positions={JSON.stringify(positions)} data-options={JSON.stringify(pathOptions)}>
      {children}
    </div>
  )),
  Marker: vi.fn(({ position, icon }: { position: unknown; icon: L.DivIcon }) => {
    // Extract HTML from Leaflet DivIcon
    const html = icon?.options?.html || '';
    return (
      <div data-testid="hex-label-marker" data-position={JSON.stringify(position)}>
        <div dangerouslySetInnerHTML={{ __html: html as string }} />
      </div>
    );
  }),
  SVGOverlay: vi.fn(({ children, bounds }: { children?: React.ReactNode; bounds: unknown }) => (
    <div data-testid="svg-overlay" data-bounds={JSON.stringify(bounds)}>
      {children}
    </div>
  )),
  LayerGroup: vi.fn(({ children }: { children?: React.ReactNode }) => (
    <div data-testid="layer-group">{children}</div>
  )),
}));

// Mock Leaflet's divIcon
vi.mock('leaflet', async (importOriginal) => {
  const L = await importOriginal<typeof import('leaflet')>();
  return {
    ...L,
    divIcon: vi.fn((options: L.DivIconOptions) => ({
      options,
    })),
    latLng: vi.fn((lat: number, lng: number) => ({ lat, lng })),
  };
});

describe('HexGridLayer', () => {
  it('renders without crashing', () => {
    const { container } = render(<HexGridLayer />);
    expect(container).toBeDefined();
  });

  it('renders a layer group container', () => {
    const { getByTestId } = render(<HexGridLayer />);
    expect(getByTestId('layer-group')).toBeInTheDocument();
  });

  it('renders hex polygons for visible viewport', () => {
    const { getAllByTestId } = render(<HexGridLayer />);
    const polygons = getAllByTestId('hex-polygon');
    expect(polygons.length).toBeGreaterThan(0);
  });

  it('renders hex polygons with correct stroke styling', () => {
    const { getAllByTestId } = render(<HexGridLayer />);
    const polygons = getAllByTestId('hex-polygon');
    
    // Check that polygons have stroke options
    const firstPolygon = polygons[0];
    const options = JSON.parse(firstPolygon.getAttribute('data-options') || '{}');
    
    expect(options.stroke).toBe(true);
    expect(options.fill).toBe(false);
  });

  it('includes coordinate labels inside hexes', () => {
    const { container } = render(<HexGridLayer />);
    
    // Look for text elements with coordinate format "q, r, s"
    // The label should contain comma-separated numbers
    const textContent = container.textContent || '';
    expect(textContent).toMatch(/-?\d+,\s*-?\d+,\s*-?\d+/);
  });

  it('renders label markers for each hex', () => {
    const { getAllByTestId } = render(<HexGridLayer />);
    
    // Check for label markers (rendered as Marker components with DivIcons)
    const labelMarkers = getAllByTestId('hex-label-marker');
    expect(labelMarkers.length).toBeGreaterThan(0);
  });

  describe('label styling', () => {
    it('renders labels with white text and black text-shadow', () => {
      const { getAllByTestId } = render(<HexGridLayer />);
      
      // Labels are rendered as span elements inside Marker DivIcons
      const labelMarkers = getAllByTestId('hex-label-marker');
      expect(labelMarkers.length).toBeGreaterThan(0);
      
      const firstLabel = labelMarkers[0];
      const span = firstLabel.querySelector('span');
      expect(span).toBeTruthy();
      
      const style = span?.getAttribute('style') || '';
      // Should have white color
      expect(style).toContain('color: white');
      // Should have text-shadow for outline effect
      expect(style).toContain('text-shadow');
    });

    it('uses small font size for labels', () => {
      const { getAllByTestId } = render(<HexGridLayer />);
      
      const labelMarkers = getAllByTestId('hex-label-marker');
      const firstLabel = labelMarkers[0];
      const span = firstLabel.querySelector('span');
      
      const style = span?.getAttribute('style') || '';
      // Font size should be specified and small
      expect(style).toContain('font-size: 9px');
    });
  });

  describe('zoom behavior', () => {
    it('accepts showLabelsAtZoom prop to control label visibility', () => {
      // Component should accept a prop to control at what zoom labels appear
      const { container } = render(<HexGridLayer showLabelsAtZoom={13} />);
      expect(container).toBeDefined();
    });

    it('accepts minZoom prop to control grid visibility', () => {
      // Component should accept a prop to control minimum zoom for grid
      const { container } = render(<HexGridLayer minZoom={10} />);
      expect(container).toBeDefined();
    });
  });
});
