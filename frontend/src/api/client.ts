import type { Farm, ZoneStatus, AnalysisRun, EvidenceItem, Recommendation } from './types';
import * as fixtures from './fixtures';

export const IS_DEMO_MODE = true; // Hardcode to true for prototyping/hackathon demo per requirements

export class ApiClient {
  private async delay(ms: number) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  async createFarm(farm: Partial<Farm>, idempotencyKey: string): Promise<{request_id: string, farm: Farm}> {
    if (IS_DEMO_MODE) {
      await this.delay(800);
      return { request_id: idempotencyKey, farm: { ...fixtures.FIXTURE_FARM, ...farm } as Farm };
    }
    throw new Error("Not implemented");
  }

  async getFarm(_farmId: string): Promise<{request_id: string, farm: Farm, latest_analysis?: AnalysisRun}> {
    if (IS_DEMO_MODE) {
      await this.delay(500);
      return { request_id: 'req-1', farm: fixtures.FIXTURE_FARM, latest_analysis: fixtures.FIXTURE_ANALYSIS_RUN };
    }
    throw new Error("Not implemented");
  }

  async analyzeFarm(_farmId: string, idempotencyKey: string): Promise<{request_id: string, analysis_run: AnalysisRun}> {
    if (IS_DEMO_MODE) {
      await this.delay(1000);
      return { request_id: idempotencyKey, analysis_run: fixtures.FIXTURE_ANALYSIS_RUN };
    }
    throw new Error("Not implemented");
  }

  async getZones(farmId: string, _analysisRunId?: string): Promise<{request_id: string, farm_id: string, zones: ZoneStatus[]}> {
    if (IS_DEMO_MODE) {
      await this.delay(800);
      return { request_id: 'req-2', farm_id: farmId, zones: fixtures.FIXTURE_ZONES };
    }
    throw new Error("Not implemented");
  }

  async getZoneEvidence(_zoneId: string): Promise<{request_id: string, evidence: EvidenceItem[]}> {
    if (IS_DEMO_MODE) {
      await this.delay(500);
      return { request_id: 'req-3', evidence: fixtures.FIXTURE_EVIDENCE };
    }
    throw new Error("Not implemented");
  }

  async getZoneRecommendation(_zoneId: string): Promise<{request_id: string, recommendation: Recommendation}> {
    if (IS_DEMO_MODE) {
      await this.delay(500);
      return { request_id: 'req-4', recommendation: fixtures.FIXTURE_RECOMMENDATION };
    }
    throw new Error("Not implemented");
  }
}

export const apiClient = new ApiClient();
