import { useEffect } from 'react';
import { MapContainer, TileLayer, Polygon, useMap } from 'react-leaflet';
import type { ZoneStatus, Farm } from '../../api/types';
import L from 'leaflet';

interface DashboardMapProps {
  farm: Farm;
  zones: ZoneStatus[];
  selectedZoneId?: string;
  onZoneSelect: (zoneId: string) => void;
}

const RISK_COLORS = {
  low: '#4caf50',
  moderate: '#ff9800',
  high: '#f44336',
  unknown: '#9e9e9e'
};

function MapFitter({ bounds }: { bounds: L.LatLngBoundsExpression }) {
  const map = useMap();
  useEffect(() => {
    map.fitBounds(bounds, { padding: [20, 20] });
  }, [map, bounds]);
  return null;
}

export default function DashboardMap({ farm, zones, selectedZoneId, onZoneSelect }: DashboardMapProps) {
  // Flip [lng, lat] to [lat, lng] for Leaflet
  const farmPositions: [number, number][] = farm.boundary.coordinates[0].map(
    coord => [coord[1], coord[0]] as [number, number]
  );
  
  const bounds = L.latLngBounds(farmPositions);

  return (
    <div className="h-[500px] w-full rounded-lg overflow-hidden border border-gray-300 shadow-sm relative z-0">
      <MapContainer 
        bounds={bounds}
        style={{ height: '100%', width: '100%' }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        
        {/* Farm Boundary */}
        <Polygon 
          positions={farmPositions} 
          pathOptions={{ color: '#000', weight: 2, fillOpacity: 0, dashArray: '5, 5' }} 
        />

        {/* Zones */}
        {zones.map(z => {
          const zonePositions: [number, number][] = z.zone.geometry.coordinates[0].map(
            coord => [coord[1], coord[0]] as [number, number]
          );
          
          let riskColor = RISK_COLORS.unknown;
          if (z.latest_prediction?.status === 'complete') {
            riskColor = RISK_COLORS[z.latest_prediction.risk_level] || RISK_COLORS.unknown;
          }

          const isSelected = selectedZoneId === z.zone.id;

          return (
            <Polygon
              key={z.zone.id}
              positions={zonePositions}
              pathOptions={{ 
                color: isSelected ? '#fff' : riskColor, 
                weight: isSelected ? 3 : 1, 
                fillColor: riskColor, 
                fillOpacity: 0.6 
              }}
              eventHandlers={{
                click: () => onZoneSelect(z.zone.id)
              }}
            />
          );
        })}
        
        <MapFitter bounds={bounds} />
      </MapContainer>
    </div>
  );
}
