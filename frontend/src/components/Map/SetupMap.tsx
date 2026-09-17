import { useEffect, useRef } from 'react';
import { MapContainer, TileLayer, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import '@geoman-io/leaflet-geoman-free/dist/leaflet-geoman.css';
import L from 'leaflet';
import '@geoman-io/leaflet-geoman-free';

// Fix leaflet icon path issues in React
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

interface SetupMapProps {
  onBoundaryChange: (boundary: number[][][] | null, center: [number, number] | null) => void;
}

function GeomanControl({ onBoundaryChange }: SetupMapProps) {
  const map = useMap();
  const drawnItems = useRef(new L.FeatureGroup());

  useEffect(() => {
    map.addLayer(drawnItems.current);
    
    map.pm.addControls({
      position: 'topleft',
      drawMarker: false,
      drawCircleMarker: false,
      drawPolyline: false,
      drawRectangle: true,
      drawPolygon: true,
      drawCircle: false,
      drawText: false,
      editMode: true,
      dragMode: true,
      cutPolygon: false,
      removalMode: true,
    });

    const updateBoundary = () => {
      const layers = drawnItems.current.getLayers();
      if (layers.length === 0) {
        onBoundaryChange(null, null);
        return;
      }
      
      // Get the first polygon (restrict to 1 farm boundary for now)
      const layer = layers[0] as L.Polygon;
      const geojson = layer.toGeoJSON();
      if (geojson.geometry.type === 'Polygon') {
        const center = layer.getBounds().getCenter();
        // GeoJSON uses [lng, lat], our contract uses [lng, lat]
        onBoundaryChange(geojson.geometry.coordinates as number[][][], [center.lng, center.lat]);
      }
    };

    map.on('pm:create', (e) => {
      // Clear existing layers to ensure only one boundary
      drawnItems.current.clearLayers();
      drawnItems.current.addLayer(e.layer);
      
      e.layer.on('pm:edit', updateBoundary);
      e.layer.on('pm:dragend', updateBoundary);
      updateBoundary();
    });

    map.on('pm:remove', (e) => {
      drawnItems.current.removeLayer(e.layer);
      updateBoundary();
    });

    return () => {
      map.pm.removeControls();
      map.removeLayer(drawnItems.current);
    };
  }, [map, onBoundaryChange]);

  return null;
}

export default function SetupMap({ onBoundaryChange }: SetupMapProps) {
  return (
    <div className="h-[400px] w-full rounded-lg overflow-hidden border border-gray-300 shadow-sm">
      <MapContainer 
        center={[10.8505, 76.2711]} // Default to Tamil Nadu region
        zoom={7} 
        style={{ height: '100%', width: '100%' }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <GeomanControl onBoundaryChange={onBoundaryChange} />
      </MapContainer>
    </div>
  );
}
