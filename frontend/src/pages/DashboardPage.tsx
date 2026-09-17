import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { apiClient } from '../api/client';
import type { Farm, ZoneStatus, AnalysisRun } from '../api/types';
import DashboardMap from '../components/Map/DashboardMap';
import { Loader2, AlertTriangle, ArrowRight, RefreshCw, CheckCircle, Info } from 'lucide-react';

export default function DashboardPage() {
  const { farmId } = useParams<{ farmId: string }>();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [farm, setFarm] = useState<Farm | null>(null);
  const [zones, setZones] = useState<ZoneStatus[]>([]);
  const [run, setRun] = useState<AnalysisRun | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!farmId) return;
    loadFarmData();
  }, [farmId]);

  const loadFarmData = async () => {
    try {
      setLoading(true);
      const { farm, latest_analysis } = await apiClient.getFarm(farmId!);
      setFarm(farm);
      if (latest_analysis) {
        setRun(latest_analysis);
        if (latest_analysis.status === 'completed' || latest_analysis.status === 'partial') {
          const { zones } = await apiClient.getZones(farmId!, latest_analysis.id);
          setZones(zones);
        }
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load farm data.');
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyze = async () => {
    if (!farmId) return;
    try {
      setAnalyzing(true);
      const idempotencyKey = crypto.randomUUID();
      const res = await apiClient.analyzeFarm(farmId, idempotencyKey);
      setRun(res.analysis_run);
      // Mock polling delay
      setTimeout(() => {
        loadFarmData();
        setAnalyzing(false);
      }, 2000);
    } catch (err: any) {
      setError(err.message);
      setAnalyzing(false);
    }
  };

  if (loading) {
    return <div className="p-10 flex justify-center"><Loader2 className="animate-spin text-farm-DEFAULT" size={48} /></div>;
  }

  if (error || !farm) {
    return <div className="p-10 text-red-500 font-bold">Error: {error}</div>;
  }

  const zonesNeedingAttention = zones.filter(z => 
    z.latest_prediction?.risk_level === 'high' || z.latest_prediction?.risk_level === 'moderate'
  );

  return (
    <div className="max-w-6xl mx-auto p-6 w-full space-y-8">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">{farm.name}</h1>
          <p className="text-gray-600">Crop: <span className="capitalize font-medium">{farm.crop}</span> | Sown: {farm.sowing_date}</p>
        </div>
        <button 
          onClick={handleAnalyze}
          disabled={analyzing}
          className="bg-farm-DEFAULT hover:bg-farm-dark text-white px-6 py-2 rounded-md font-medium shadow flex items-center gap-2 disabled:opacity-70"
        >
          {analyzing ? <Loader2 className="animate-spin" size={18} /> : <RefreshCw size={18} />}
          {analyzing ? 'Analyzing...' : 'Run Analysis'}
        </button>
      </div>

      {!run && !analyzing && (
        <div className="bg-blue-50 p-6 rounded-lg border border-blue-200 flex items-start gap-4">
          <Info className="text-blue-500 shrink-0 mt-1" />
          <div>
            <h3 className="font-bold text-blue-900">No analysis available yet</h3>
            <p className="text-blue-800 text-sm mt-1">Click "Run Analysis" to fetch satellite and weather data and generate the digital farm twin.</p>
          </div>
        </div>
      )}

      {run && (
        <div className="grid lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 space-y-4">
            <h2 className="text-xl font-bold">Digital Farm Twin</h2>
            <DashboardMap farm={farm} zones={zones} onZoneSelect={(id) => navigate(`/farms/${farm.id}/zones/${id}`)} />
            
            <div className="flex gap-4 text-sm font-medium pt-2">
              <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-risk-low inline-block"></span> Low Risk</span>
              <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-risk-moderate inline-block"></span> Moderate Risk</span>
              <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-risk-high inline-block"></span> High Risk</span>
              <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-risk-unknown inline-block"></span> Unknown / Insufficient Data</span>
            </div>
          </div>

          <div className="space-y-4">
            <h2 className="text-xl font-bold">What needs attention?</h2>
            
            {zones.length === 0 && run.status === 'completed' && (
              <p className="text-gray-500 italic">No zones generated.</p>
            )}

            {zonesNeedingAttention.length === 0 && zones.length > 0 && (
              <div className="bg-green-50 p-4 rounded-lg border border-green-200 flex items-center gap-3">
                <CheckCircle className="text-green-500 shrink-0" />
                <p className="text-green-800 font-medium">All zones look healthy.</p>
              </div>
            )}

            <div className="space-y-4">
              {zonesNeedingAttention.map(z => (
                <div key={z.zone.id} className="border border-gray-200 rounded-lg p-4 bg-white shadow-sm hover:shadow-md transition-shadow cursor-pointer" onClick={() => navigate(`/farms/${farm.id}/zones/${z.zone.id}`)}>
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="font-bold">Zone {z.zone.id.substring(0,6)}...</h3>
                    <span className={`text-xs font-bold px-2 py-1 rounded uppercase ${z.latest_prediction?.risk_level === 'high' ? 'bg-red-100 text-red-800' : 'bg-orange-100 text-orange-800'}`}>
                      {z.latest_prediction?.risk_level} RISK
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 mb-3">Confidence: <span className="font-semibold capitalize">{z.latest_prediction?.confidence.level}</span></p>
                  
                  <div className="text-sm flex items-center text-farm-DEFAULT font-medium group">
                    Analyze Zone <ArrowRight size={16} className="ml-1 transition-transform group-hover:translate-x-1" />
                  </div>
                </div>
              ))}
            </div>
            
            {run.status === 'partial' && (
              <div className="mt-6 bg-yellow-50 p-4 border-l-4 border-yellow-400 rounded">
                <p className="text-yellow-800 text-sm font-medium flex items-center gap-2">
                  <AlertTriangle size={16} /> Analysis completed partially due to missing upstream data.
                </p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
