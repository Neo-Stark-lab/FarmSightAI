import type { Farm, ZoneStatus, EvidenceItem, Recommendation, AnalysisRun } from './types';

// The adapter layer isolates backend response structures from UI components.
// We pass the typed API responses through these adapters so we can gracefully handle
// any structural changes from the backend.

export const adaptFarm = (data: any): Farm => {
  return data as Farm;
};

export const adaptAnalysisRun = (data: any): AnalysisRun => {
  return data as AnalysisRun;
};

export const adaptZones = (data: any[]): ZoneStatus[] => {
  return data.map(zone => zone as ZoneStatus);
};

export const adaptEvidence = (data: any[]): EvidenceItem[] => {
  return data.map(item => item as EvidenceItem);
};

export const adaptRecommendation = (data: any): Recommendation => {
  return data as Recommendation;
};
