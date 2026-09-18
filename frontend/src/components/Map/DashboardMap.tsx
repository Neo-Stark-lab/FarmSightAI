import { useEffect, useState, useMemo } from 'react';
import { MapContainer, TileLayer, Polygon, useMap } from 'react-leaflet';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowRight, Layers } from 'lucide-react';
import type { ZoneStatus, Farm } from '../../api/types';
import L from 'leaflet';

interface DashboardMapProps {
  farm: Farm;
  zones: ZoneStatus[];
  onZoneClick: (zoneId: string) => void;
}

const RISK_COLORS = {
  low: '#2e7d32',
  moderate: '#d97706',
  high: '#dc2626',
  unknown: '#737373'
};

function MapFitter({ bounds }: { bounds: L.LatLngBoundsExpression }) {
  const map = useMap();
  useEffect(() => {
    map.fitBounds(bounds, { padding: [40, 40], maxZoom: 18 });
  }, [map, bounds]);
  return null;
}

export default function DashboardMap({ farm, zones, onZoneClick }: DashboardMapProps) {
  const [hoveredZoneId, setHoveredZoneId] = useState<string | null>(null);
  const [activeLayer, setActiveLayer] = useState<'water_stress'>('water_stress');
  
  // Flip [lng, lat] to [lat, lng] for Leaflet
  const farmPositions: [number, number][] = useMemo(() => {
    return farm.boundary.coordinates[0].map(
      coord => [coord[1], coord[0]] as [number, number]
    );
  }, [farm.boundary]);
  
  const bounds = useMemo(() => L.latLngBounds(farmPositions), [farmPositions]);

  // Find hovered zone for the floating card
  const hoveredZone = useMemo(() => zones.find(z => z.zone.id === hoveredZoneId), [hoveredZoneId, zones]);

  const colorMatch = useMemo(() => {
    if (!hoveredZone || hoveredZone.latest_prediction?.status !== 'valid') {
      return { base: 'bg-gray-500', text: 'text-gray-700' };
    }
    const risk = hoveredZone.latest_prediction.risk_level;
    switch (risk) {
      case 'high': return { base: 'bg-red-600', text: 'text-red-700' };
      case 'moderate': return { base: 'bg-orange-500', text: 'text-orange-700' };
      case 'low': return { base: 'bg-green-600', text: 'text-green-700' };
      default: return { base: 'bg-gray-500', text: 'text-gray-700' };
    }
  }, [hoveredZone]);

  return (
    <div className="h-full w-full relative z-0 bg-gray-100">
      <MapContainer 
        bounds={bounds}
        style={{ height: '100%', width: '100%', background: '#e5e7eb' }}
        zoomControl={false}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png" // Cleaner, lighter basemap
        />
        
        {/* Farm Boundary */}
        <Polygon 
          positions={farmPositions} 
          pathOptions={{ color: '#1b4332', weight: 2, fillOpacity: 0, dashArray: '6, 6' }} 
        />

        {/* Zones */}
        {zones.map(z => {
          const zonePositions: [number, number][] = z.zone.geometry.coordinates[0].map(
            coord => [coord[1], coord[0]] as [number, number]
          );
          
          let riskColor = RISK_COLORS.unknown;
          if (z.latest_prediction?.status === 'valid') {
            riskColor = RISK_COLORS[z.latest_prediction.risk_level] || RISK_COLORS.unknown;
          }

          const isHovered = hoveredZoneId === z.zone.id;
          const hasHover = hoveredZoneId !== null;
          const opacity = hasHover && !isHovered ? 0.4 : isHovered ? 0.8 : 0.65;

          return (
            <Polygon
              key={z.zone.id}
              positions={zonePositions}
              pathOptions={{ 
                color: isHovered ? '#ffffff' : riskColor, 
                weight: isHovered ? 3 : 1, 
                fillColor: riskColor, 
                fillOpacity: opacity,
                transition: 'fill-opacity 0.25s ease'
              } as any}
              eventHandlers={{
                mouseover: () => setHoveredZoneId(z.zone.id),
                mouseout: () => setHoveredZoneId(null),
                click: () => onZoneClick(z.zone.id)
              }}
            />
          );
        })}
        
        <MapFitter bounds={bounds} />
      </MapContainer>

      {/* Layer Control Overlay */}
      <div className="absolute top-6 right-6 z-[400]">
        <div className="bg-white/90 backdrop-blur-md rounded-xl shadow-lg border border-white/50 p-2 min-w-[160px]">
          <div className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-2 px-2 pt-1 flex items-center gap-1">
            <Layers size={14} /> VIEW
          </div>
          <div className="space-y-1">
            <button 
              className={`w-full text-left px-3 py-1.5 rounded-lg text-sm font-medium flex items-center gap-2 transition-colors ${activeLayer === 'water_stress' ? 'bg-farm-light text-farm-dark' : 'text-gray-600 hover:bg-gray-100'}`}
              onClick={() => setActiveLayer('water_stress')}
            >
              <div className={`w-2 h-2 rounded-full ${activeLayer === 'water_stress' ? 'bg-farm-DEFAULT' : 'bg-gray-300'}`} />
              Water Stress
            </button>
            {/* The prompt specifically states: "Do not fabricate raster/map layers... If only water-stress zones are currently available, show only Water Stress" */}
          </div>
        </div>
      </div>

      {/* Hover Floating Glass Card */}
      <AnimatePresence>
        {hoveredZone && (
          <motion.div 
            initial={{ opacity: 0, y: 8, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 8, scale: 0.98 }}
            transition={{ duration: 0.25, ease: "easeOut" }}
            className="absolute top-6 left-6 z-[400] pointer-events-none"
          >
            <div className="bg-white/95 backdrop-blur-xl rounded-2xl shadow-xl shadow-gray-900/10 border border-white/50 p-5 w-64">
              <div className="flex justify-between items-start mb-1">
                <span className="text-xs font-bold text-gray-400 uppercase tracking-widest">ZONE {hoveredZone.zone.id.substring(0,4)}</span>
              </div>
              
              {hoveredZone.latest_prediction?.status === 'valid' ? (
                <>
                  <h3 className={`font-bold text-lg leading-tight mb-3 capitalize ${
                    hoveredZone.latest_prediction.risk_level === 'high' ? 'text-red-700' :
                    hoveredZone.latest_prediction.risk_level === 'moderate' ? 'text-orange-700' :
                    'text-farm-dark'
                  }`}>
                    {hoveredZone.latest_prediction.risk_level} Risk
                  </h3>
                  
                  <div className="flex justify-between items-baseline mb-1">
                    <span className="text-3xl font-bold tracking-tighter text-gray-900">
                      {((hoveredZone.latest_prediction.probability ?? 0) * 100).toFixed(1)}<span className="text-lg text-gray-400">%</span>
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-1.5 mt-2 overflow-hidden">
                    <div 
                      className={`h-1.5 rounded-full ${colorMatch.base}`}
                      style={{ width: `${(hoveredZone.latest_prediction.probability ?? 0) * 100}%` }}
                    />
                  </div>
                  <p className="text-xs font-medium text-gray-500 capitalize mb-4 mt-2">
                    {hoveredZone.latest_prediction.confidence.level} confidence
                  </p>
                </>
              ) : (
                <div className="py-4">
                  <h3 className="font-bold text-gray-900 text-lg leading-tight mb-2">Insufficient Data</h3>
                  <p className="text-xs text-gray-500">Not enough data to calculate probability.</p>
                </div>
              )}
              
              <div className="pt-3 border-t border-gray-100 flex items-center text-sm font-semibold text-farm-DEFAULT">
                View analysis <ArrowRight size={16} className="ml-1" />
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
