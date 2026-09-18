import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { apiClient } from '../api/client';
import type { ZoneStatus, EvidenceItem, Recommendation } from '../api/types';
import { Loader2, ArrowLeft, ArrowUpRight, ArrowDownRight, Minus, Clock, Database, AlertCircle, Cpu, Sprout } from 'lucide-react';

export default function ZoneDetailPage() {
  const { farmId, zoneId } = useParams<{ farmId: string, zoneId: string }>();
  const [loading, setLoading] = useState(true);
  const [zone, setZone] = useState<ZoneStatus | null>(null);
  const [evidence, setEvidence] = useState<EvidenceItem[]>([]);
  const [recommendation, setRecommendation] = useState<Recommendation | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        const { zones } = await apiClient.getZones(farmId!);
        const z = zones.find(z => z.zone.id === zoneId);
        if (!z) throw new Error("Zone not found");
        setZone(z);
        
        const [evRes, recRes] = await Promise.all([
          apiClient.getZoneEvidence(zoneId!),
          apiClient.getZoneRecommendation(zoneId!)
        ]);
        setEvidence(evRes.evidence);
        setRecommendation(recRes.recommendation);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, [farmId, zoneId]);

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center bg-surface">
      <Loader2 className="animate-spin text-farm-DEFAULT" size={48} />
    </div>
  );

  if (error || !zone) return (
    <div className="min-h-screen flex items-center justify-center bg-surface">
      <div className="bg-red-50 p-8 rounded-2xl border border-red-200 text-center">
        <AlertCircle className="text-red-500 mx-auto mb-4" size={48} />
        <h2 className="text-2xl font-bold text-red-900 mb-2">Error Loading Zone</h2>
        <p className="text-red-700">{error || "Zone not found"}</p>
        <Link to={`/farms/${farmId}`} className="mt-6 inline-flex items-center text-red-700 font-medium hover:underline">
          <ArrowLeft size={16} className="mr-1" /> Return to Farm
        </Link>
      </div>
    </div>
  );

  const pred = zone.latest_prediction;
  const isHighRisk = pred?.risk_level === 'high';
  const isModerateRisk = pred?.risk_level === 'moderate';
  const isLowRisk = pred?.risk_level === 'low';
  const isInsufficient = pred?.status === 'insufficient_data' || !pred;

  const riskColorClass = isHighRisk ? 'text-red-600' : isModerateRisk ? 'text-orange-500' : isLowRisk ? 'text-farm-DEFAULT' : 'text-gray-400';
  const bgRiskColorClass = isHighRisk ? 'bg-red-50 border-red-100' : isModerateRisk ? 'bg-orange-50 border-orange-100' : isLowRisk ? 'bg-farm-light/50 border-farm-light' : 'bg-gray-50 border-gray-100';

  return (
    <div className="bg-surface min-h-screen pb-20">
      {/* Header */}
      <div className="bg-white border-b border-gray-100 sticky top-0 z-10 shadow-sm">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div>
            <Link to={`/farms/${farmId}`} className="text-gray-500 flex items-center gap-1 font-medium hover:text-gray-900 transition-colors mb-1 text-sm">
              <ArrowLeft size={16} /> Back to Digital Farm Twin
            </Link>
            <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Zone Focus: {zone.zone.id.substring(0,6)}...</h1>
          </div>
          {/* Status Badge */}
          <div className={`px-4 py-1.5 rounded-full border text-sm font-bold uppercase tracking-wider ${
            isHighRisk ? 'bg-red-50 border-red-200 text-red-700' : 
            isModerateRisk ? 'bg-orange-50 border-orange-200 text-orange-700' : 
            isLowRisk ? 'bg-green-50 border-green-200 text-green-700' : 
            'bg-gray-100 border-gray-200 text-gray-700'
          }`}>
            {isInsufficient ? 'Insufficient Data' : `${pred.risk_level} Risk`}
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-6 py-8">
        <div className="grid lg:grid-cols-12 gap-8">
          
          {/* Left Column: Summary & Explainability (8 cols) */}
          <div className="lg:col-span-8 space-y-8">
            
            {/* Risk & Confidence Hero Card */}
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className={`p-8 rounded-3xl border shadow-sm relative overflow-hidden ${bgRiskColorClass}`}>
              <div className="absolute top-0 right-0 w-64 h-64 bg-white/40 blur-3xl rounded-full -mr-20 -mt-20 pointer-events-none" />
              
              <div className="grid md:grid-cols-2 gap-8 relative z-10">
                <div>
                  <h2 className="text-sm font-bold text-gray-500 uppercase tracking-widest mb-2">Water-Stress Probability</h2>
                  {pred?.probability !== null && pred?.probability !== undefined ? (
                    <div className="flex items-baseline gap-1 mb-2">
                      <span className={`text-6xl font-extrabold tracking-tighter ${riskColorClass}`}>
                        {(pred.probability * 100).toFixed(1)}
                      </span>
                      <span className={`text-2xl font-bold ${riskColorClass} opacity-60`}>%</span>
                    </div>
                  ) : (
                    <div className="text-3xl font-bold text-gray-400 mb-2 mt-4">N/A</div>
                  )}
                  <p className="text-gray-600 font-medium">Model confidence is <span className="capitalize font-bold text-gray-900">{pred?.confidence.level || 'Unknown'}</span></p>
                  <p className="text-xs text-gray-400 mt-2 leading-relaxed">
                    Confidence reflects the availability and freshness of supporting data. It is not the probability that the prediction is correct.
                  </p>
                </div>
                
                <div className="flex flex-col justify-end space-y-3">
                  <div className="bg-white/60 p-4 rounded-xl border border-white/50 backdrop-blur-sm">
                    <h4 className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-1">Basis</h4>
                    <p className="text-sm font-medium text-gray-800">
                      {pred?.confidence.basis && pred.confidence.basis.length > 0 
                        ? pred.confidence.basis.join(', ')
                        : 'No valid basis available.'}
                    </p>
                  </div>
                </div>
              </div>
            </motion.div>

            {/* Recommendation Alert Block */}
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
              <div className="bg-white rounded-3xl p-8 border border-gray-200 shadow-sm relative overflow-hidden group">
                <div className="absolute top-0 left-0 w-1 h-full bg-farm-DEFAULT transition-all group-hover:w-2" />
                
                <div className="flex items-start gap-4 mb-6">
                  <div className="w-12 h-12 bg-farm-light text-farm-DEFAULT rounded-xl flex items-center justify-center shrink-0">
                    <Sprout size={24} />
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-gray-900">Intelligence Recommendation</h3>
                    <p className="text-gray-500 text-sm">Automated agronomic advice based on SHAP contributors.</p>
                  </div>
                </div>

                {recommendation?.status === 'active' || recommendation?.status === 'available' ? (
                  <div className="space-y-6">
                    <div className="text-2xl font-bold text-gray-900 tracking-tight">
                      {(recommendation.action_type || recommendation.action) === 'PRIORITIZE_FIELD_CHECK'
                        ? 'Check this field first'
                        : (recommendation.action_type || recommendation.action)}
                    </div>
                    
                    {(recommendation.explanation || (recommendation.explanations && recommendation.explanations.length > 0)) && (
                      <div className="bg-gray-50 p-6 rounded-2xl border border-gray-100">
                        <h4 className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-3">Why?</h4>
                        <ul className="space-y-2 text-gray-700 font-medium">
                          {recommendation.explanation && <li className="flex items-start gap-2"><ArrowRightIcon /> <span>{recommendation.explanation}</span></li>}
                          {recommendation.explanations && recommendation.explanations.map((exp, idx) => (
                            <li key={idx} className="flex items-start gap-2"><ArrowRightIcon /> <span>{exp}</span></li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {recommendation.limitations && recommendation.limitations.length > 0 && (
                      <div className="bg-orange-50 p-4 rounded-xl text-sm text-orange-900 flex items-start gap-3 border border-orange-200">
                        <AlertCircle size={18} className="shrink-0 mt-0.5 text-orange-600" />
                        <div className="font-medium">
                          {recommendation.limitations.map((lim, idx) => <p key={idx}>{lim}</p>)}
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="bg-gray-50 p-6 rounded-2xl border border-gray-100 text-center">
                    <p className="text-gray-500 font-medium">No recommendation available for this zone. Data may be insufficient.</p>
                  </div>
                )}
              </div>
            </motion.div>

            {/* AI Explainability (SHAP) */}
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
              <div className="bg-white rounded-3xl p-8 border border-gray-200 shadow-sm">
                <div className="flex items-start justify-between mb-8">
                  <div>
                    <h3 className="text-xl font-bold text-gray-900 flex items-center gap-2">
                      <Cpu size={24} className="text-blue-500" />
                      What is influencing this risk?
                    </h3>
                    <p className="text-gray-500 text-sm mt-1">
                      These factors influence the model's assessment. Factors shown as increasing risk push the assessment toward higher water-stress risk; decreasing factors push it away.
                    </p>
                  </div>
                </div>
                
                <div className="space-y-4">
                  {pred?.contributions?.map((c, idx) => {
                    const isIncreases = c.direction === 'increases_risk';
                    const isDecreases = c.direction === 'decreases_risk';
                    
                    return (
                      <div key={idx} className="flex items-center gap-4 p-4 rounded-2xl bg-gray-50 border border-gray-100 transition-colors hover:bg-gray-100/50">
                        <div className={`p-3 rounded-xl shadow-sm ${isIncreases ? 'bg-red-100 text-red-600' : isDecreases ? 'bg-green-100 text-green-600' : 'bg-gray-200 text-gray-600'}`}>
                          {isIncreases ? <ArrowUpRight size={24} /> : isDecreases ? <ArrowDownRight size={24} /> : <Minus size={24} />}
                        </div>
                        <div className="flex-1">
                          <p className={`text-xs font-bold uppercase tracking-wider mb-1 ${isIncreases ? 'text-red-700' : isDecreases ? 'text-green-700' : 'text-gray-600'}`}>
                            {isIncreases ? 'Increases Risk' : isDecreases ? 'Decreases Risk' : 'Neutral Impact'}
                          </p>
                          <p className="text-lg font-bold text-gray-900 capitalize tracking-tight">{c.feature.replace(/_/g, ' ')}</p>
                        </div>
                      </div>
                    )
                  })}
                  {(!pred?.contributions || pred.contributions.length === 0) && (
                    <div className="text-center p-8 border border-dashed border-gray-300 rounded-2xl">
                      <p className="text-gray-500 font-medium">No explainability factors available for this prediction.</p>
                    </div>
                  )}
                </div>
              </div>
            </motion.div>

          </div>

          {/* Right Column: Evidence & Metadata (4 cols) */}
          <div className="lg:col-span-4 space-y-6">
            
            {/* Freshness Card */}
            <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.1 }}>
              <div className="bg-white p-6 rounded-2xl border border-gray-200 shadow-sm">
                <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2"><Clock size={18} className="text-blue-500"/> Data Freshness</h3>
                <div className="space-y-4">
                  {zone.data_freshness?.items.map((item, idx) => (
                    <div key={idx} className="flex justify-between items-center text-sm">
                      <span className="capitalize font-medium text-gray-700">{item.signal_type}</span>
                      <span className={`px-2.5 py-1 rounded-md text-xs font-bold tracking-wide uppercase ${
                        item.status === 'fresh' ? 'bg-green-100 text-green-800' : 
                        item.status === 'stale' ? 'bg-yellow-100 text-yellow-800' : 
                        'bg-red-100 text-red-800'
                      }`}>
                        {item.status}
                      </span>
                    </div>
                  ))}
                  {(!zone.data_freshness?.items || zone.data_freshness.items.length === 0) && (
                    <p className="text-xs text-gray-500 italic">No freshness metadata.</p>
                  )}
                </div>
              </div>
            </motion.div>

            {/* Evidence Data Card */}
            <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.2 }}>
              <div className="bg-white p-6 rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
                <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2"><Database size={18} className="text-purple-500"/> Feature Evidence</h3>
                <div className="space-y-1 -mx-2">
                  {evidence.map((ev, idx) => (
                    <div key={idx} className="flex flex-col p-2 hover:bg-gray-50 rounded-lg transition-colors">
                      <span className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-0.5">{ev.feature_name.replace(/_/g, ' ')}</span>
                      <div className="flex justify-between items-end">
                        <span className="font-bold text-gray-900">
                          {ev.value !== null ? `${ev.value} ${ev.unit}` : <span className="text-gray-400 font-medium italic">Missing</span>}
                        </span>
                        <span className="text-xs text-gray-400 font-medium truncate max-w-[100px]" title={typeof ev.source === 'object' && ev.source ? ev.source.provider : ev.source}>
                          {typeof ev.source === 'object' && ev.source ? ev.source.provider : ev.source}
                        </span>
                      </div>
                    </div>
                  ))}
                  {evidence.length === 0 && (
                    <div className="p-4 text-center">
                      <p className="text-gray-500 text-sm">No raw evidence available.</p>
                    </div>
                  )}
                </div>
              </div>
            </motion.div>

          </div>
        </div>
      </div>
    </div>
  );
}

function ArrowRightIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-farm-DEFAULT mt-1 shrink-0">
      <path d="M5 12h14" />
      <path d="m12 5 7 7-7 7" />
    </svg>
  );
}
