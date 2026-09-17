export type RiskLevel = 'low' | 'moderate' | 'high' | 'unknown';
export type ConfidenceLevel = 'low' | 'medium' | 'high';
export type AnalysisStatus = 'queued' | 'running' | 'completed' | 'partial' | 'failed';

export interface Point {
  type: 'Point';
  coordinates: [number, number]; // [longitude, latitude]
}

export interface Polygon {
  type: 'Polygon';
  coordinates: number[][][];
}

export interface Farm {
  id: string;
  name: string;
  location: Point;
  boundary: Polygon;
  crop: 'rice' | 'groundnut' | 'maize';
  sowing_date: string;
  timezone: string;
}

export interface Zone {
  id: string;
  farm_id: string;
  geometry: Polygon;
  area_hectares: number;
}

export interface Prediction {
  prediction_type: string;
  risk_level: RiskLevel;
  confidence: {
    level: ConfidenceLevel;
    score?: number;
    basis: string[];
  };
  probability?: number;
  contributions?: {
    feature: string;
    direction: 'increases_risk' | 'decreases_risk' | 'neutral' | 'unknown';
    magnitude: number;
    method: string;
    source_observation_ids: string[];
  }[];
  status: 'complete' | 'insufficient_data' | 'failed';
}

export interface DataFreshness {
  overall_status: 'fresh' | 'stale' | 'missing';
  items: {
    signal_type: string;
    status: 'fresh' | 'stale' | 'missing' | 'unavailable';
    last_observation_time: string | null;
    source: string;
  }[];
}

export interface ZoneStatus {
  zone: Zone;
  latest_prediction?: Prediction;
  data_freshness?: DataFreshness;
  recommendation_status?: 'available' | 'not_available';
}

export interface AnalysisRun {
  id: string;
  farm_id: string;
  status: AnalysisStatus;
  requested_at: string;
  analysis_reference_time: string;
  failure_code?: string;
  failure_message?: string;
}

export interface EvidenceItem {
  feature_name: string;
  value: number;
  unit: string;
  source: string;
  observation_time: string;
  quality_flags: string[];
}

export interface Recommendation {
  status: 'available' | 'not_available';
  action: string | null;
  limitations: string[];
  explanations?: string[];
}
