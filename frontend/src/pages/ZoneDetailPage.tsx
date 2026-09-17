import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { apiClient } from '../api/client';
import type { ZoneStatus, EvidenceItem, Recommendation } from '../api/types';
import { Loader2, ArrowLeft, ArrowUp, ArrowDown, Minus, Clock, ShieldAlert, Database, AlertCircle } from 'lucide-react';

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
        // In a real app we might pass run ID, but fixture returns deterministically
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

  if (loading) return <div className="p-10 flex justify-center"><Loader2 className="animate-spin text-farm-DEFAULT" size={48} /></div>;
  if (error || !zone) return <div className="p-10 text-red-500 font-bold">Error: {error}</div>;

  const pred = zone.latest_prediction;
  const isHighRisk = pred?.risk_level === 'high';
  const isModerateRisk = pred?.risk_level === 'moderate';

  return (
    <div className="max-w-5xl mx-auto p-6 w-full space-y-8">
      <div>
        <Link to={`/farms/${farmId}`} className="text-farm-DEFAULT flex items-center gap-1 font-medium hover:underline mb-4">
          <ArrowLeft size={16} /> Back to Digital Farm Twin
        </Link>
        <h1 className="text-3xl font-bold text-gray-900">Zone {zone.zone.id.substring(0,8)}</h1>
      </div>

      <div className="grid md:grid-cols-3 gap-6">
        {/* Risk & Confidence Overview */}
        <div className="md:col-span-1 space-y-6">
          <div className={`p-6 rounded-xl border ${isHighRisk ? 'bg-red-50 border-red-200' : isModerateRisk ? 'bg-orange-50 border-orange-200' : 'bg-green-50 border-green-200'}`}>
            <p className="text-sm uppercase font-bold text-gray-500 mb-1">Water-Stress Risk</p>
            <h2 className={`text-4xl font-extrabold capitalize ${isHighRisk ? 'text-red-700' : isModerateRisk ? 'text-orange-700' : 'text-green-700'}`}>
              {pred?.risk_level || 'Unknown'}
            </h2>
            
            <div className="mt-6 pt-4 border-t border-black/10">
              {pred?.probability !== null && pred?.probability !== undefined && (
                <p className="text-sm font-bold text-gray-600 mb-1 flex items-center gap-2">
                  <ShieldAlert size={16} /> Risk probability: <span className="text-black">{(pred.probability * 100).toFixed(1)}%</span>
                </p>
              )}
              <p className="text-sm font-bold text-gray-600 mb-1 flex items-center gap-2">
                <ShieldAlert size={16} /> Confidence: <span className="capitalize text-black">{pred?.confidence.level || 'Unknown'}</span>
              </p>
              {pred?.confidence.basis && pred.confidence.basis.length > 0 && (
                <p className="text-xs text-gray-500 mt-1">Based on: {pred.confidence.basis.join(', ')}</p>
              )}
            </div>
          </div>

          <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
            <h3 className="font-bold mb-4 flex items-center gap-2"><Clock size={18}/> Data Freshness</h3>
            <div className="space-y-3">
              {zone.data_freshness?.items.map((item, idx) => (
                <div key={idx} className="flex justify-between items-center text-sm border-b pb-2 last:border-0 last:pb-0">
                  <span className="capitalize font-medium text-gray-700">{item.signal_type}</span>
                  <span className={`px-2 py-0.5 rounded text-xs font-bold ${
                    item.status === 'fresh' ? 'bg-green-100 text-green-800' : 
                    item.status === 'stale' ? 'bg-yellow-100 text-yellow-800' : 
                    'bg-red-100 text-red-800'
                  }`}>
                    {item.status.toUpperCase()}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Explainability & Action */}
        <div className="md:col-span-2 space-y-6">
          <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
            <h3 className="text-xl font-bold mb-4">Why is this zone flagged?</h3>
            <p className="text-sm text-gray-600 mb-6">Machine learning contributions relative to HIGH water-stress risk.</p>
            
            <div className="space-y-3">
              {pred?.contributions?.map((c, idx) => {
                const isIncreases = c.direction === 'increases_risk';
                const isDecreases = c.direction === 'decreases_risk';
                
                return (
                  <div key={idx} className="flex items-center gap-4 p-3 rounded-lg bg-gray-50 border border-gray-100">
                    <div className={`p-2 rounded-full ${isIncreases ? 'bg-red-100 text-red-600' : isDecreases ? 'bg-green-100 text-green-600' : 'bg-gray-200 text-gray-600'}`}>
                      {isIncreases ? <ArrowUp size={20} /> : isDecreases ? <ArrowDown size={20} /> : <Minus size={20} />}
                    </div>
                    <div>
                      <p className={`text-sm font-bold ${isIncreases ? 'text-red-700' : isDecreases ? 'text-green-700' : 'text-gray-700'}`}>
                        {isIncreases ? 'Increases Risk' : isDecreases ? 'Decreases Risk' : 'Neutral'}
                      </p>
                      <p className="text-lg font-medium text-gray-900 capitalize">{c.feature.replace(/_/g, ' ')}</p>
                    </div>
                  </div>
                )
              })}
              {(!pred?.contributions || pred.contributions.length === 0) && (
                <p className="text-gray-500 italic">No explainability factors available for this prediction.</p>
              )}
            </div>
          </div>

          <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
            <h3 className="text-xl font-bold mb-4">Evidence Data</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead className="bg-gray-50 text-gray-700 uppercase">
                  <tr>
                    <th className="px-4 py-3 rounded-tl-lg">Feature</th>
                    <th className="px-4 py-3">Value</th>
                    <th className="px-4 py-3">Source</th>
                  </tr>
                </thead>
                <tbody>
                  {evidence.map((ev, idx) => (
                    <tr key={idx} className="border-b last:border-0">
                      <td className="px-4 py-3 font-medium text-gray-900 capitalize">{ev.feature_name.replace(/_/g, ' ')}</td>
                      <td className="px-4 py-3">{ev.value !== null ? `${ev.value} ${ev.unit}` : <span className="text-gray-400">Missing</span>}</td>
                      <td className="px-4 py-3 flex items-center gap-1 text-gray-500"><Database size={14}/> {typeof ev.source === 'object' && ev.source ? ev.source.provider : ev.source}</td>
                    </tr>
                  ))}
                  {evidence.length === 0 && (
                    <tr><td colSpan={3} className="px-4 py-4 text-center text-gray-500">No raw evidence available.</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          <div className="bg-farm-light p-6 rounded-xl border border-farm-DEFAULT/30 shadow-sm">
            <h3 className="text-xl font-bold mb-4 text-farm-dark">Agricultural Recommendation</h3>
            {recommendation?.status === 'active' || recommendation?.status === 'available' ? (
              <div className="space-y-4">
                <div className="bg-white p-4 rounded-lg border border-farm-DEFAULT/20 shadow-sm">
                  <p className="font-bold text-gray-900 text-lg">{recommendation.action_type || recommendation.action}</p>
                </div>
                
                {(recommendation.explanation || (recommendation.explanations && recommendation.explanations.length > 0)) && (
                  <div>
                    <h4 className="text-sm font-bold text-gray-700 uppercase mb-2">Why?</h4>
                    <ul className="list-disc pl-5 text-gray-600 space-y-1">
                      {recommendation.explanation && <li>{recommendation.explanation}</li>}
                      {recommendation.explanations && recommendation.explanations.map((exp, idx) => <li key={idx}>{exp}</li>)}
                    </ul>
                  </div>
                )}

                {recommendation.limitations && recommendation.limitations.length > 0 && (
                  <div className="bg-orange-50 p-3 rounded text-sm text-orange-800 flex items-start gap-2 border border-orange-200">
                    <AlertCircle size={16} className="shrink-0 mt-0.5" />
                    <div>
                      {recommendation.limitations.map((lim, idx) => <p key={idx}>{lim}</p>)}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-gray-500 italic">No recommendation available for this zone. Data may be insufficient.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
