import { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { apiClient } from '../api/client';
import type { Farm, ZoneStatus, AnalysisRun } from '../api/types';
import DashboardMap from '../components/Map/DashboardMap';
import { Loader2, AlertTriangle, ArrowRight, RefreshCw, CheckCircle, Info, XCircle, Map as MapIcon, CloudRain, Cpu, Activity, FileWarning } from 'lucide-react';

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
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load farm data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let timeoutId: ReturnType<typeof setTimeout>;
    let isSubscribed = true;

    const checkRunState = async () => {
      if (!run || !farmId || !isSubscribed) return;
      
      if (run.status === 'queued' || run.status === 'running') {
        setAnalyzing(true);
        timeoutId = setTimeout(async () => {
          try {
            const res = await apiClient.getAnalysisRun(run.id);
            if (isSubscribed) setRun(res.analysis_run);
          } catch (err: any) {
            if (isSubscribed) {
              setError(err.message || 'Polling failed');
              setAnalyzing(false);
            }
          }
        }, 2000);
      } else if (run.status === 'completed' || run.status === 'partial') {
        setAnalyzing(false);
        try {
          const { zones: fetchedZones } = await apiClient.getZones(farmId, run.id);
          if (isSubscribed) setZones(fetchedZones);
        } catch (err: any) {
          if (isSubscribed) setError(err.message || 'Failed to fetch zones');
        }
      } else if (run.status === 'failed') {
        setAnalyzing(false);
      }
    };

    checkRunState();

    return () => {
      isSubscribed = false;
      clearTimeout(timeoutId);
    };
  }, [run?.status, run?.id, farmId]);

  const analyzeKeyRef = useRef<string | null>(null);

  const handleAnalyze = async () => {
    if (!farmId) return;
    try {
      setAnalyzing(true);
      setError(null);
      if (!analyzeKeyRef.current) {
        analyzeKeyRef.current = crypto.randomUUID();
      }
      const res = await apiClient.analyzeFarm(farmId, analyzeKeyRef.current);
      setRun(res.analysis_run);
      analyzeKeyRef.current = null;
    } catch (err: any) {
      setError(err.message);
      setAnalyzing(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-surface">
        <Loader2 className="animate-spin text-farm-DEFAULT" size={48} />
      </div>
    );
  }

  if (!farm) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-surface">
        <div className="bg-red-50 p-8 rounded-2xl border border-red-200 text-center">
          <AlertTriangle className="text-red-500 mx-auto mb-4" size={48} />
          <h2 className="text-2xl font-bold text-red-900 mb-2">Farm Not Found</h2>
          <p className="text-red-700">The requested Digital Farm Twin could not be loaded.</p>
        </div>
      </div>
    );
  }

  const zonesNeedingAttention = zones.filter(z => 
    z.latest_prediction?.status === 'valid' && 
    (z.latest_prediction?.risk_level === 'high' || z.latest_prediction?.risk_level === 'moderate')
  );

  const unknownZones = zones.filter(z => 
    z.latest_prediction?.status === 'insufficient_data' || 
    !z.latest_prediction || 
    z.latest_prediction?.risk_level === 'unknown'
  );

  // Compute farm-level summary for the cards
  const attentionCount = zonesNeedingAttention.length + unknownZones.length;
  const highestRisk = zonesNeedingAttention.some(z => z.latest_prediction?.risk_level === 'high') ? 'High' : 
                      zonesNeedingAttention.length > 0 ? 'Moderate' : 'Low';

  return (
    <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }} className="w-full h-[calc(100vh-73px)] flex flex-col bg-surface overflow-hidden">
      
      {/* Header */}
      <div className="shrink-0 px-6 py-4 bg-white border-b border-gray-100 flex justify-between items-center z-10">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 tracking-tight">{farm.name}</h1>
          <p className="text-sm text-gray-500 font-medium">
            {zones.reduce((sum, z) => sum + z.zone.area_hectares, 0).toFixed(2)} ha &middot; <span className="capitalize">{farm.crop}</span> &middot; Sown {new Date(farm.sowing_date).toLocaleDateString(undefined, { day: 'numeric', month: 'short' })}
          </p>
        </div>
        
        <button 
          onClick={handleAnalyze}
          disabled={analyzing}
          className="bg-gray-900 hover:bg-black text-white px-6 py-2.5 rounded-xl font-medium shadow-md shadow-gray-900/10 flex items-center gap-2 disabled:opacity-50 transition-all hover:scale-[1.02] active:scale-[0.98]"
        >
          {analyzing ? <Loader2 className="animate-spin" size={18} /> : <RefreshCw size={18} />}
          {analyzing ? 'Analyzing...' : 'Run Analysis'}
        </button>
      </div>

      {/* Main Layout - Split screen on desktop */}
      <div className="flex-1 flex flex-col lg:flex-row overflow-hidden relative">
        
        {/* Left Side: Map Hero (approx 65-75%) */}
        <div className="w-full lg:w-[65%] xl:w-[70%] h-[50vh] lg:h-full relative bg-gray-100 border-r border-gray-200">
          <DashboardMap farm={farm} zones={zones} onZoneClick={(id: string) => navigate(`/farms/${farm.id}/zones/${id}`)} />
          
          {/* Map Legend (Floating overlay) */}
          <div className="absolute bottom-6 left-6 z-[400] bg-white/90 backdrop-blur-md p-3 rounded-xl shadow-lg border border-white/50 text-xs font-semibold space-y-2 pointer-events-none">
            <div className="flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-risk-low"></span> LOW</div>
            <div className="flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-risk-moderate"></span> MODERATE</div>
            <div className="flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-risk-high"></span> HIGH</div>
            <div className="flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-risk-unknown"></span> INSUFFICIENT DATA</div>
          </div>
        </div>

        {/* Right Side: Intelligence & States (Scrollable) */}
        <div className="w-full lg:w-[35%] xl:w-[30%] h-[50vh] lg:h-full overflow-y-auto bg-surface p-6 z-10">
          
          {error && (
            <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="bg-red-50 border border-red-200 p-4 rounded-xl mb-6 shadow-sm flex items-start gap-3">
              <AlertTriangle className="text-red-500 shrink-0 mt-0.5" />
              <div>
                <h4 className="text-red-900 font-bold">Error</h4>
                <p className="text-red-700 text-sm mt-1">{error}</p>
              </div>
            </motion.div>
          )}

          {/* Loading / Processing State Overlay Equivalent */}
          <AnimatePresence mode="wait">
            {(!run && !analyzing) && (
              <motion.div key="no-run" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="mb-8">
                <div className="bg-white border border-gray-100 p-8 rounded-3xl text-center shadow-sm">
                  <div className="w-16 h-16 bg-farm-light rounded-2xl flex items-center justify-center mx-auto mb-4 text-farm-DEFAULT">
                    <Info size={32} />
                  </div>
                  <h3 className="font-bold text-gray-900 text-xl mb-2">Ready for analysis</h3>
                  <p className="text-gray-500 text-sm mb-6">Run an analysis to gather live satellite and weather observations for this farm.</p>
                  <button onClick={handleAnalyze} className="bg-farm-DEFAULT hover:bg-farm-secondary text-white font-medium py-2.5 px-6 rounded-full transition-colors w-full flex justify-center items-center gap-2">
                    Start Analysis <ArrowRight size={18} />
                  </button>
                </div>
              </motion.div>
            )}

            {analyzing && run && (run.status === 'queued' || run.status === 'running') && (
              <motion.div key="analyzing" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="mb-8">
                <div className="bg-white border border-gray-100 p-8 rounded-3xl shadow-sm">
                  <div className="flex justify-center mb-6">
                    <div className="w-16 h-16 rounded-full bg-blue-50 flex items-center justify-center relative">
                      <Loader2 className="absolute animate-spin text-blue-500" size={32} />
                      <Cpu size={20} className="text-blue-500" />
                    </div>
                  </div>
                  <h3 className="font-bold text-gray-900 text-xl text-center mb-6">Analyzing your farm</h3>
                  
                  <div className="space-y-4 text-sm font-medium">
                    <div className="flex items-center justify-between text-gray-700">
                      <span className="flex items-center gap-2"><MapIcon size={16} /> Satellite imagery</span>
                      {run.status === 'running' ? <CheckCircle size={16} className="text-farm-DEFAULT" /> : <Loader2 size={16} className="animate-spin text-gray-400" />}
                    </div>
                    <div className="flex items-center justify-between text-gray-700">
                      <span className="flex items-center gap-2"><CloudRain size={16} /> Weather conditions</span>
                      {run.status === 'running' ? <CheckCircle size={16} className="text-farm-DEFAULT" /> : <Loader2 size={16} className="animate-spin text-gray-400" />}
                    </div>
                    <div className="flex items-center justify-between text-gray-700">
                      <span className="flex items-center gap-2"><Activity size={16} /> Water-stress model</span>
                      <Loader2 size={16} className="animate-spin text-blue-500" />
                    </div>
                  </div>
                </div>
              </motion.div>
            )}

            {run && run.status === 'failed' && (
              <motion.div key="failed" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mb-8">
                <div className="bg-red-50 p-6 rounded-2xl border border-red-200 flex items-start gap-4">
                  <XCircle className="text-red-500 shrink-0 mt-1" />
                  <div>
                    <h3 className="font-bold text-red-900">Analysis could not be completed.</h3>
                    <p className="text-red-800 text-sm mt-1">Please try running the analysis again or check data provider status.</p>
                  </div>
                </div>
              </motion.div>
            )}

            {run && (run.status === 'completed' || run.status === 'partial') && !analyzing && (
              <motion.div key="results" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
                
                {/* Summary Cards */}
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-white p-4 rounded-2xl border border-gray-100 shadow-sm flex flex-col justify-center">
                    <span className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-1">Attention</span>
                    <span className="text-2xl font-bold text-gray-900">{attentionCount} <span className="text-sm font-medium text-gray-500">zones</span></span>
                  </div>
                  <div className="bg-white p-4 rounded-2xl border border-gray-100 shadow-sm flex flex-col justify-center">
                    <span className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-1">Farm Risk</span>
                    <span className={`text-xl font-bold ${highestRisk === 'High' ? 'text-red-600' : highestRisk === 'Moderate' ? 'text-orange-500' : 'text-farm-DEFAULT'}`}>
                      {highestRisk}
                    </span>
                  </div>
                </div>

                {run.status === 'partial' && (
                  <div className="bg-amber-50 p-4 rounded-xl border border-amber-200 flex items-start gap-3">
                    <FileWarning className="text-amber-600 shrink-0 mt-0.5" size={18} />
                    <p className="text-amber-800 text-sm font-medium">Analysis completed with missing or stale supporting data.</p>
                  </div>
                )}

                <div className="pt-2">
                  <h2 className="text-xl font-bold text-gray-900 mb-4 tracking-tight">What needs attention?</h2>
                  
                  {zones.length === 0 && (
                    <p className="text-gray-500 italic p-4 bg-white rounded-xl border border-gray-100 text-center">No zones generated.</p>
                  )}

                  {zonesNeedingAttention.length === 0 && unknownZones.length === 0 && zones.length > 0 && (
                    <div className="bg-farm-light/50 p-6 rounded-2xl border border-farm-light flex flex-col items-center justify-center text-center">
                      <CheckCircle className="text-farm-DEFAULT mb-3" size={32} />
                      <h3 className="font-bold text-farm-dark text-lg mb-1">All zones look healthy</h3>
                      <p className="text-farm-secondary text-sm">No significant water-stress indicators detected.</p>
                    </div>
                  )}

                  <div className="space-y-3">
                    {zonesNeedingAttention.map((z, idx) => (
                      <motion.div 
                        initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: idx * 0.1 }}
                        key={z.zone.id} 
                        onClick={() => navigate(`/farms/${farm.id}/zones/${z.zone.id}`)}
                        className="bg-white border border-gray-100 rounded-2xl p-4 shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all cursor-pointer group"
                      >
                        <div className="flex justify-between items-start mb-2">
                          <h3 className="font-bold text-gray-900">Zone {z.zone.id.substring(0,4)}</h3>
                          <span className={`text-xs font-bold px-2 py-1 rounded-full uppercase tracking-wider ${z.latest_prediction?.risk_level === 'high' ? 'bg-red-50 text-red-700' : 'bg-orange-50 text-orange-700'}`}>
                            {z.latest_prediction?.risk_level} RISK
                          </span>
                        </div>
                        <p className="text-sm text-gray-600 font-medium mb-3">
                          {z.latest_prediction?.risk_level === 'high' ? 'High water-stress indicators detected.' : 'Moderate water-stress indicators detected.'}
                        </p>
                        <div className="flex justify-between items-end">
                          <p className="text-xs text-gray-500">Confidence: <span className="font-semibold capitalize text-gray-700">{z.latest_prediction?.confidence.level}</span></p>
                          <div className="text-sm font-semibold text-farm-DEFAULT flex items-center">
                            View <ArrowRight size={16} className="ml-1 transition-transform group-hover:translate-x-1" />
                          </div>
                        </div>
                      </motion.div>
                    ))}

                    {/* Insufficient Data Zones */}
                    {unknownZones.map((z, idx) => (
                      <motion.div 
                        initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: (zonesNeedingAttention.length + idx) * 0.1 }}
                        key={z.zone.id} 
                        onClick={() => navigate(`/farms/${farm.id}/zones/${z.zone.id}`)}
                        className="bg-gray-50 border border-gray-200 rounded-2xl p-4 hover:shadow-sm hover:-translate-y-0.5 transition-all cursor-pointer group"
                      >
                        <div className="flex justify-between items-start mb-2">
                          <h3 className="font-bold text-gray-900">Zone {z.zone.id.substring(0,4)}</h3>
                          <span className="text-xs font-bold px-2 py-1 rounded-full bg-gray-200 text-gray-700 uppercase tracking-wider">
                            INSUFFICIENT DATA
                          </span>
                        </div>
                        <p className="text-sm text-gray-600 font-medium mb-3">
                          Not enough supporting data for a reliable assessment.
                        </p>
                        <div className="flex justify-between items-end">
                          <div />
                          <div className="text-sm font-semibold text-gray-700 flex items-center">
                            View <ArrowRight size={16} className="ml-1 transition-transform group-hover:translate-x-1" />
                          </div>
                        </div>
                      </motion.div>
                    ))}
                  </div>
                </div>

              </motion.div>
            )}
          </AnimatePresence>

        </div>
      </div>
    </motion.div>
  );
}
