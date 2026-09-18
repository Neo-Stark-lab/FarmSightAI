import type { Farm, ZoneStatus, AnalysisRun, EvidenceItem, Recommendation } from './types';
import * as fixtures from './fixtures';
import { adaptAnalysisRun, adaptPredictionStatus } from './adapters';

export const IS_DEMO_MODE = import.meta.env.VITE_API_MODE === 'demo';
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const API_PREFIX = '/api/v1';

export class ApiClient {
  private async delay(ms: number) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  private async fetchBackend(path: string, options: RequestInit = {}) {
    const response = await fetch(`${API_URL}${API_PREFIX}${path}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });
    if (!response.ok) {
      if (response.status === 409) {
        throw new Error('idempotency_conflict: Idempotency-Key was already used with a different request');
      }
      const data = await response.json().catch(() => ({}));
      throw new Error(data.error?.message || `HTTP ${response.status}`);
    }
    return response.json();
  }

  async getUserFarms(userId: string): Promise<{request_id: string, farms: Farm[]}> {
    if (IS_DEMO_MODE) {
      await this.delay(500);
      return { request_id: 'req-list', farms: [fixtures.FIXTURE_FARM] };
    }
    const data = await this.fetchBackend(`/users/${userId}/farms`);
    return { request_id: data.request_id, farms: data.farms };
  }

  async createFarm(farm: Partial<Farm>, idempotencyKey: string, userId?: string): Promise<{request_id: string, farm: Farm}> {
    if (IS_DEMO_MODE) {
      await this.delay(800);
      return { request_id: idempotencyKey, farm: { ...fixtures.FIXTURE_FARM, ...farm, id: String(Date.now()) } as Farm };
    }
    const headers: Record<string, string> = { 'Idempotency-Key': idempotencyKey };
    if (userId) {
      headers['X-Demo-User-Id'] = userId;
    }
    const data = await this.fetchBackend('/farms', {
      method: 'POST',
      headers,
      body: JSON.stringify(farm)
    });
    return { request_id: data.request_id, farm: data.farm };
  }

  async getFarm(farmId: string): Promise<{request_id: string, farm: Farm, latest_analysis?: AnalysisRun}> {
    if (IS_DEMO_MODE) {
      await this.delay(500);
      return { request_id: 'req-1', farm: fixtures.FIXTURE_FARM, latest_analysis: fixtures.FIXTURE_ANALYSIS_RUN };
    }
    const data = await this.fetchBackend(`/farms/${farmId}`);
    return { 
      request_id: data.request_id, 
      farm: data.farm, 
      latest_analysis: data.latest_analysis ? adaptAnalysisRun(data.latest_analysis) : undefined 
    };
  }

  async analyzeFarm(farmId: string, idempotencyKey: string): Promise<{request_id: string, analysis_run: AnalysisRun}> {
    if (IS_DEMO_MODE) {
      await this.delay(1000);
      return { request_id: idempotencyKey, analysis_run: fixtures.FIXTURE_ANALYSIS_RUN };
    }
    const data = await this.fetchBackend(`/farms/${farmId}/analyze`, {
      method: 'POST',
      headers: { 'Idempotency-Key': idempotencyKey },
      body: JSON.stringify({})
    });
    return { request_id: data.request_id, analysis_run: adaptAnalysisRun(data.analysis_run) };
  }

  async getAnalysisRun(runId: string): Promise<{request_id: string, analysis_run: AnalysisRun}> {
    if (IS_DEMO_MODE) {
      await this.delay(300);
      return { request_id: 'req', analysis_run: fixtures.FIXTURE_ANALYSIS_RUN };
    }
    const data = await this.fetchBackend(`/analysis-runs/${runId}`);
    return { request_id: data.request_id, analysis_run: adaptAnalysisRun(data.analysis_run) };
  }

  async getZones(farmId: string, analysisRunId?: string): Promise<{request_id: string, farm_id: string, zones: ZoneStatus[]}> {
    if (IS_DEMO_MODE) {
      await this.delay(800);
      return { request_id: 'req-2', farm_id: farmId, zones: fixtures.FIXTURE_ZONES };
    }
    const url = analysisRunId ? `/farms/${farmId}/zones?analysis_run_id=${analysisRunId}` : `/farms/${farmId}/zones`;
    const data = await this.fetchBackend(url);
    // Adapt statuses
    const zones = data.zones.map((z: any) => {
        if (z.latest_prediction) {
             z.latest_prediction = adaptPredictionStatus(z.latest_prediction);
        }
        return z;
    });
    return { request_id: data.request_id, farm_id: data.farm_id, zones };
  }

  async getZoneEvidence(zoneId: string, analysisRunId?: string): Promise<{request_id: string, prediction: any, evidence: EvidenceItem[], data_freshness: any, limitations: string[]}> {
    if (IS_DEMO_MODE) {
      await this.delay(500);
      return { request_id: 'req-3', prediction: fixtures.FIXTURE_ZONES[0].latest_prediction, evidence: fixtures.FIXTURE_EVIDENCE, data_freshness: fixtures.FIXTURE_ZONES[0].data_freshness, limitations: fixtures.FIXTURE_RECOMMENDATION.limitations };
    }
    const url = analysisRunId ? `/zones/${zoneId}/evidence?analysis_run_id=${analysisRunId}` : `/zones/${zoneId}/evidence`;
    const data = await this.fetchBackend(url);
    if (data.prediction) {
       data.prediction = adaptPredictionStatus(data.prediction);
    }
    return data;
  }

  async getZoneRecommendation(zoneId: string, analysisRunId?: string): Promise<{request_id: string, recommendation: Recommendation}> {
    if (IS_DEMO_MODE) {
      await this.delay(500);
      return { request_id: 'req-4', recommendation: fixtures.FIXTURE_RECOMMENDATION };
    }
    const url = analysisRunId ? `/zones/${zoneId}/recommendation?analysis_run_id=${analysisRunId}` : `/zones/${zoneId}/recommendation`;
    const data = await this.fetchBackend(url);
    return data;
  }
}

export const apiClient = new ApiClient();
