import '@testing-library/jest-dom';
import { vi } from 'vitest';

// Mock Leaflet as it requires a real DOM heavily
vi.mock('react-leaflet', async () => {
  return {
    MapContainer: ({ children }: any) => <div data-testid="map-container">{children}</div>,
    TileLayer: () => <div data-testid="tile-layer" />,
    FeatureGroup: ({ children }: any) => <div data-testid="feature-group">{children}</div>,
    Polygon: () => <div data-testid="polygon" />,
    useMap: () => ({
      addLayer: vi.fn(),
      removeLayer: vi.fn(),
      fitBounds: vi.fn(),
      on: vi.fn(),
      off: vi.fn(),
      pm: {
        addControls: vi.fn(),
        removeControls: vi.fn()
      }
    })
  };
});

// Mock geoman
vi.mock('@geoman-io/leaflet-geoman-free', () => ({}));
