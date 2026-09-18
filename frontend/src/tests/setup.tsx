import '@testing-library/jest-dom';
import { vi } from 'vitest';

// Fix Node 22+ native localStorage conflicting with Vitest/jsdom.
// Node 22 introduces global localStorage, but without --localstorage-file it lacks
// standard methods like clear(), causing TypeError: localStorage.clear is not a function.
const mockStorage = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => { store[key] = value.toString(); },
    removeItem: (key: string) => { delete store[key]; },
    clear: () => { store = {}; },
    key: (index: number) => Object.keys(store)[index] || null,
    get length() { return Object.keys(store).length; }
  };
})();

Object.defineProperty(globalThis, 'localStorage', { value: mockStorage, configurable: true, writable: true });
if (typeof window !== 'undefined') {
  Object.defineProperty(window, 'localStorage', { value: mockStorage, configurable: true, writable: true });
}

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
