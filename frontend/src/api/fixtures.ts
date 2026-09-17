import type { Farm, ZoneStatus, AnalysisRun, EvidenceItem, Recommendation } from './types';

export const FIXTURE_FARM: Farm = {
  id: 'f-1234',
  name: 'Demo Farm (Tamil Nadu)',
  location: { type: 'Point', coordinates: [79.0, 10.5] },
  boundary: {
    type: 'Polygon',
    coordinates: [[
      [79.001, 10.501],
      [79.002, 10.501],
      [79.002, 10.502],
      [79.001, 10.502],
      [79.001, 10.501]
    ]]
  },
  crop: 'rice',
  sowing_date: '2026-08-01',
  timezone: 'Asia/Kolkata'
};

export const FIXTURE_ANALYSIS_RUN: AnalysisRun = {
  id: 'a-9999',
  farm_id: 'f-1234',
  status: 'completed',
  requested_at: new Date().toISOString(),
  analysis_reference_time: new Date().toISOString()
};

export const FIXTURE_ZONES: ZoneStatus[] = [
  {
    zone: {
      id: 'z-1',
      farm_id: 'f-1234',
      geometry: {
        type: 'Polygon',
        coordinates: [[
          [79.001, 10.501],
          [79.0015, 10.501],
          [79.0015, 10.502],
          [79.001, 10.502],
          [79.001, 10.501]
        ]]
      },
      area_hectares: 1.2
    },
    latest_prediction: {
      prediction_type: 'water_stress_risk',
      risk_level: 'high',
      confidence: {
        level: 'high',
        basis: ['fresh_satellite', 'fresh_weather']
      },
      probability: 0.85,
      contributions: [
        { feature: 'soil_moisture', direction: 'increases_risk', magnitude: 0.15, method: 'shap', source_observation_ids: [] },
        { feature: 'rainfall_30d', direction: 'increases_risk', magnitude: 0.12, method: 'shap', source_observation_ids: [] },
        { feature: 'ndvi_current', direction: 'increases_risk', magnitude: 0.08, method: 'shap', source_observation_ids: [] }
      ],
      status: 'valid'
    },
    data_freshness: {
      overall_status: 'fresh',
      items: [
        { signal_type: 'satellite', status: 'fresh', last_observation_time: new Date().toISOString(), source: 'sentinel-2' },
        { signal_type: 'weather', status: 'fresh', last_observation_time: new Date().toISOString(), source: 'open-meteo' }
      ]
    },
    recommendation_status: 'available'
  },
  {
    zone: {
      id: 'z-2',
      farm_id: 'f-1234',
      geometry: {
        type: 'Polygon',
        coordinates: [[
          [79.0015, 10.501],
          [79.002, 10.501],
          [79.002, 10.502],
          [79.0015, 10.502],
          [79.0015, 10.501]
        ]]
      },
      area_hectares: 1.2
    },
    latest_prediction: {
      prediction_type: 'water_stress_risk',
      risk_level: 'low',
      confidence: {
        level: 'medium',
        basis: ['stale_satellite', 'fresh_weather']
      },
      contributions: [
        { feature: 'rainfall_30d', direction: 'decreases_risk', magnitude: 0.10, method: 'shap', source_observation_ids: [] }
      ],
      status: 'valid'
    },
    data_freshness: {
      overall_status: 'stale',
      items: [
        { signal_type: 'satellite', status: 'stale', last_observation_time: new Date(Date.now() - 864000000).toISOString(), source: 'sentinel-2' },
        { signal_type: 'weather', status: 'fresh', last_observation_time: new Date().toISOString(), source: 'open-meteo' }
      ]
    },
    recommendation_status: 'available'
  }
];

export const FIXTURE_EVIDENCE: EvidenceItem[] = [
  {
    feature_name: 'soil_moisture',
    value: 0.12,
    unit: 'm3/m3',
    source: 'era5-land',
    observation_time: new Date().toISOString(),
    quality_flags: []
  },
  {
    feature_name: 'rainfall_30d',
    value: 45.2,
    unit: 'mm',
    source: 'open-meteo',
    observation_time: new Date().toISOString(),
    quality_flags: []
  }
];

export const FIXTURE_RECOMMENDATION: Recommendation = {
  status: 'available',
  action: 'Schedule supplemental irrigation within 48 hours to prevent yield loss during the tillering stage.',
  limitations: ['Recommendation based on modeled coarse soil moisture, verify field conditions.'],
  explanations: ['High water stress detected combined with lack of recent rainfall.']
};
