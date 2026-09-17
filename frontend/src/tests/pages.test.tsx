import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import FarmSetupPage from '../pages/FarmSetupPage';
import DashboardPage from '../pages/DashboardPage';
import ZoneDetailPage from '../pages/ZoneDetailPage';
import { apiClient } from '../api/client';
import { FIXTURE_FARM, FIXTURE_ANALYSIS_RUN, FIXTURE_ZONES, FIXTURE_EVIDENCE, FIXTURE_RECOMMENDATION } from '../api/fixtures';

// Mock the API client
vi.mock('../api/client', () => ({
  apiClient: {
    createFarm: vi.fn(),
    getFarm: vi.fn(),
    analyzeFarm: vi.fn(),
    getZones: vi.fn(),
    getZoneEvidence: vi.fn(),
    getZoneRecommendation: vi.fn(),
  }
}));

// Mock crypto.randomUUID for predictable but trackable keys
let uuidCounter = 0;
Object.defineProperty(globalThis, 'crypto', {
  value: {
    randomUUID: () => `test-uuid-${++uuidCounter}`
  }
});

// Mock SetupMap since we can't draw in jsdom easily
vi.mock('../components/Map/SetupMap', () => {
  return {
    default: function MockSetupMap({ onBoundaryChange }: any) {
      return (
        <button 
          data-testid="mock-draw" 
          onClick={() => onBoundaryChange(
            [[[1, 1], [1, 2], [2, 2], [2, 1], [1, 1]]], 
            [1.5, 1.5]
          )}
        >
          Mock Draw Boundary
        </button>
      );
    }
  };
});

describe('Lap 5 Behavior Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    uuidCounter = 0;
  });

  describe('FARM SETUP', () => {
    it('rejects submission without boundary', async () => {
      render(
        <MemoryRouter>
          <FarmSetupPage />
        </MemoryRouter>
      );
      
      fireEvent.change(screen.getByLabelText(/Farm Name/i), { target: { value: 'Test Farm' } });
      fireEvent.change(screen.getByLabelText(/Sowing Date/i), { target: { value: '2026-08-01' } });
      
      fireEvent.click(screen.getByText(/Save & Analyze Farm/i));
      
      expect(await screen.findByText(/Please fill out all fields and draw a farm boundary/i)).toBeInTheDocument();
      expect(apiClient.createFarm).not.toHaveBeenCalled();
    });

    it('submits successfully and passes Idempotency-Key', async () => {
      vi.mocked(apiClient.createFarm).mockResolvedValueOnce({ request_id: '123', farm: FIXTURE_FARM });
      
      render(
        <MemoryRouter>
          <FarmSetupPage />
        </MemoryRouter>
      );
      
      fireEvent.change(screen.getByLabelText(/Farm Name/i), { target: { value: 'Test Farm' } });
      fireEvent.change(screen.getByLabelText(/Sowing Date/i), { target: { value: '2026-08-01' } });
      fireEvent.click(screen.getByTestId('mock-draw'));
      
      fireEvent.click(screen.getByText(/Save & Analyze Farm/i));
      
      await waitFor(() => {
        expect(apiClient.createFarm).toHaveBeenCalledWith(
          expect.objectContaining({ name: 'Test Farm' }),
          'test-uuid-1'
        );
      });
    });

    it('reuses Idempotency-Key on retry, but generates new one on input change', async () => {
      // First attempt fails
      vi.mocked(apiClient.createFarm).mockRejectedValueOnce(new Error("Network Error"));
      
      render(
        <MemoryRouter>
          <FarmSetupPage />
        </MemoryRouter>
      );
      
      fireEvent.change(screen.getByLabelText(/Farm Name/i), { target: { value: 'Test Farm' } });
      fireEvent.change(screen.getByLabelText(/Sowing Date/i), { target: { value: '2026-08-01' } });
      fireEvent.click(screen.getByTestId('mock-draw'));
      
      fireEvent.click(screen.getByText(/Save & Analyze Farm/i));
      
      await waitFor(() => expect(screen.getByText(/Network Error/i)).toBeInTheDocument());
      
      expect(apiClient.createFarm).toHaveBeenCalledWith(expect.anything(), 'test-uuid-1');
      
      // Retry (no input changes)
      vi.mocked(apiClient.createFarm).mockResolvedValueOnce({ request_id: '123', farm: FIXTURE_FARM });
      fireEvent.click(screen.getByText(/Save & Analyze Farm/i));
      
      await waitFor(() => {
        expect(apiClient.createFarm).toHaveBeenLastCalledWith(expect.anything(), 'test-uuid-1');
      });
      
      // Change input (new submission)
      fireEvent.change(screen.getByLabelText(/Farm Name/i), { target: { value: 'New Farm' } });
      fireEvent.click(screen.getByText(/Save & Analyze Farm/i));
      
      await waitFor(() => {
        expect(apiClient.createFarm).toHaveBeenLastCalledWith(expect.anything(), 'test-uuid-2');
      });
    });
  });

  describe('ANALYSIS & DASHBOARD', () => {
    it('analyzes farm, handles idempotency retries and loading states', async () => {
      vi.mocked(apiClient.getFarm).mockResolvedValue({ request_id: '1', farm: FIXTURE_FARM, latest_analysis: undefined });
      vi.mocked(apiClient.analyzeFarm).mockRejectedValueOnce(new Error("API Failed"));
      
      render(
        <MemoryRouter initialEntries={['/farms/f-1234']}>
          <Routes>
            <Route path="/farms/:farmId" element={<DashboardPage />} />
          </Routes>
        </MemoryRouter>
      );
      
      await waitFor(() => expect(screen.getByText(/No analysis available yet/i)).toBeInTheDocument());
      
      // First try - fails
      fireEvent.click(await screen.findByRole('button'));
      await waitFor(() => expect(screen.getByText(/API Failed/i)).toBeInTheDocument());
      expect(apiClient.analyzeFarm).toHaveBeenCalledWith('f-1234', 'test-uuid-1');
      
      // Retry - succeeds
      vi.mocked(apiClient.analyzeFarm).mockResolvedValueOnce({ request_id: '1', analysis_run: FIXTURE_ANALYSIS_RUN });
      vi.mocked(apiClient.getFarm).mockResolvedValue({ request_id: '1', farm: FIXTURE_FARM, latest_analysis: FIXTURE_ANALYSIS_RUN });
      vi.mocked(apiClient.getZones).mockResolvedValue({ request_id: '1', farm_id: 'f-1234', zones: FIXTURE_ZONES });
      
      fireEvent.click(await screen.findByRole('button'));
      await waitFor(() => expect(apiClient.analyzeFarm).toHaveBeenLastCalledWith('f-1234', 'test-uuid-1'));
      
      // After success, wait for polling to finish
      await waitFor(() => expect(screen.getByRole('button')).not.toBeDisabled(), { timeout: 3000 });
      
      // Trigger NEW analysis (since last one succeeded)
      vi.mocked(apiClient.analyzeFarm).mockResolvedValueOnce({ request_id: '1', analysis_run: FIXTURE_ANALYSIS_RUN });
      fireEvent.click(await screen.findByRole('button'));
      await waitFor(() => expect(apiClient.analyzeFarm).toHaveBeenLastCalledWith('f-1234', 'test-uuid-2'));
    });
  });

  describe('ZONE DETAILS (RISK, CONFIDENCE, EXPLAINABILITY, EVIDENCE)', () => {
    it('renders all required elements without fabricating probability', async () => {
      vi.mocked(apiClient.getZones).mockResolvedValue({ request_id: '1', farm_id: 'f-1234', zones: FIXTURE_ZONES });
      vi.mocked(apiClient.getZoneEvidence).mockResolvedValue({ request_id: '1', prediction: FIXTURE_ZONES[0].latest_prediction, evidence: FIXTURE_EVIDENCE, data_freshness: FIXTURE_ZONES[0].data_freshness, limitations: FIXTURE_RECOMMENDATION.limitations });
      vi.mocked(apiClient.getZoneRecommendation).mockResolvedValue({ request_id: '1', recommendation: FIXTURE_RECOMMENDATION });

      render(
        <MemoryRouter initialEntries={['/farms/f-1234/zones/z-1']}>
          <Routes>
            <Route path="/farms/:farmId/zones/:zoneId" element={<ZoneDetailPage />} />
          </Routes>
        </MemoryRouter>
      );
      
      // Wait for loading to finish
      await waitFor(() => expect(screen.getByText(/Zone z-1/i)).toBeInTheDocument());
      
      // RISK RENDERING
      expect(screen.getAllByText(/high/i).length).toBeGreaterThan(0);
      
      // CONFIDENCE RENDERING
      expect(screen.getByText(/Confidence:/i)).toBeInTheDocument();
      expect(screen.getAllByText(/high/i).length).toBeGreaterThan(0); // from fixture
      expect(screen.getByText(/85\.0%/)).toBeInTheDocument(); // Expect probability since it's in the fixture

      // EXPLAINABILITY (↑ for increases_risk)
      expect(screen.getAllByText(/Increases Risk/i).length).toBeGreaterThan(0);
      
      // EVIDENCE
      expect(screen.getAllByText(/soil moisture/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/0.12/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/era5-land/i).length).toBeGreaterThan(0);
      
      // RECOMMENDATION
      expect(screen.getByText(/Schedule supplemental irrigation/i)).toBeInTheDocument();
      expect(screen.getByText(/Recommendation based on modeled coarse soil moisture/i)).toBeInTheDocument();
    });
  });
});
