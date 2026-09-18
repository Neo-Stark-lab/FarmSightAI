import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { apiClient } from '../api/client';
import SetupMap from '../components/Map/SetupMap';
import { Sprout, Loader2, Map as MapIcon, ArrowRight, ArrowLeft, CheckCircle2 } from 'lucide-react';
import { demoFarms, demoAuth } from '../utils/demoPersistence';

export default function FarmSetupPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [name, setName] = useState('');
  const [crop, setCrop] = useState<'rice' | 'groundnut' | 'maize'>('rice');
  const [sowingDate, setSowingDate] = useState('');
  
  const [boundary, setBoundary] = useState<number[][][] | null>(null);
  const [center, setCenter] = useState<[number, number] | null>(null);

  const idempotencyKeyRef = useRef<string | null>(null);

  // A genuinely new submission clears the old key
  useEffect(() => {
    idempotencyKeyRef.current = null;
  }, [name, crop, sowingDate, boundary, center]);

  const handleNext = () => {
    if (step === 1) {
      if (!name || !sowingDate) {
        setError("Please fill out all farm details.");
        return;
      }
    }
    if (step === 2) {
      if (!boundary || !center) {
        setError("Please draw a farm boundary on the map.");
        return;
      }
    }
    setError(null);
    setStep(s => Math.min(s + 1, 3));
  };

  const handleBack = () => {
    setError(null);
    setStep(s => Math.max(s - 1, 1));
  };

  const handleSubmit = async () => {
    if (!name || !boundary || !center || !sowingDate) {
      setError("Please fill out all fields and draw a farm boundary.");
      return;
    }
    
    setLoading(true);
    setError(null);
    try {
      if (!idempotencyKeyRef.current) {
        idempotencyKeyRef.current = crypto.randomUUID();
      }
      
      const userId = demoAuth.getUserId() || undefined;

      const res = await apiClient.createFarm({
        name,
        crop,
        sowing_date: sowingDate,
        location: { type: 'Point', coordinates: center },
        boundary: { type: 'Polygon', coordinates: boundary },
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone
      }, idempotencyKeyRef.current, userId);
      
      // Save farm to demo persistence so it appears in My Farms if in demo mode
      demoFarms.addFarm(res.farm);
      
      navigate(`/farms/${res.farm.id}`);
    } catch (err: any) {
      setError(err.message || "Failed to create farm.");
      setLoading(false);
    }
  };

  const stepVariants = {
    initial: { opacity: 0, x: 20 },
    animate: { opacity: 1, x: 0, transition: { duration: 0.4 } },
    exit: { opacity: 0, x: -20, transition: { duration: 0.3 } }
  };

  return (
    <div className="flex-1 bg-surface py-12 px-6 min-h-[calc(100vh-73px)] flex flex-col items-center">
      <div className="w-full max-w-4xl">
        
        {/* Progress Indicator */}
        <div className="mb-12">
          <div className="flex items-center justify-between relative max-w-2xl mx-auto">
            <div className="absolute left-0 top-1/2 -translate-y-1/2 w-full h-1 bg-gray-200 rounded-full z-0" />
            <div 
              className="absolute left-0 top-1/2 -translate-y-1/2 h-1 bg-farm-DEFAULT rounded-full z-0 transition-all duration-500 ease-out"
              style={{ width: `${((step - 1) / 2) * 100}%` }}
            />
            
            {[
              { num: 1, label: 'Farm' },
              { num: 2, label: 'Boundary' },
              { num: 3, label: 'Review' }
            ].map(s => (
              <div key={s.num} className="relative z-10 flex flex-col items-center">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm transition-colors duration-300 ${
                  step >= s.num ? 'bg-farm-DEFAULT text-white shadow-md' : 'bg-gray-100 text-gray-400 border-2 border-white'
                }`}>
                  {step > s.num ? <CheckCircle2 size={20} /> : s.num}
                </div>
                <span className={`absolute top-12 text-xs font-medium whitespace-nowrap ${step >= s.num ? 'text-gray-900' : 'text-gray-400'}`}>
                  {s.label}
                </span>
              </div>
            ))}
          </div>
        </div>

        {error && (
          <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="bg-red-50 border border-red-200 p-4 rounded-xl mb-8 flex gap-3 text-red-800">
            <AlertTriangle className="shrink-0" />
            <p>{error}</p>
          </motion.div>
        )}

        <div className="bg-white rounded-3xl shadow-xl shadow-gray-200/50 border border-gray-100 overflow-hidden relative min-h-[500px]">
          <AnimatePresence mode="wait">
            {step === 1 && (
              <motion.div key="step1" variants={stepVariants} initial="initial" animate="animate" exit="exit" className="p-8 md:p-12">
                <div className="max-w-xl mx-auto">
                  <div className="text-center mb-10">
                    <div className="w-16 h-16 bg-farm-light text-farm-DEFAULT rounded-2xl flex items-center justify-center mx-auto mb-6">
                      <Sprout size={32} />
                    </div>
                    <h2 className="text-3xl font-bold tracking-tight text-gray-900 mb-2">Farm details</h2>
                    <p className="text-gray-500">Let's start with the basics of your farm.</p>
                  </div>

                  <div className="space-y-6">
                    <div>
                      <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">Farm Name</label>
                      <input 
                        id="name"
                        type="text" required value={name} onChange={e => setName(e.target.value)}
                        className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-farm-DEFAULT/20 focus:border-farm-DEFAULT transition-shadow bg-gray-50/50"
                        placeholder="e.g., North Field"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Crop Type</label>
                      <select 
                        value={crop} onChange={e => setCrop(e.target.value as any)}
                        className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-farm-DEFAULT/20 focus:border-farm-DEFAULT transition-shadow bg-gray-50/50 capitalize"
                      >
                        <option value="rice">Rice</option>
                        <option value="groundnut">Groundnut</option>
                        <option value="maize">Maize</option>
                      </select>
                    </div>
                    <div>
                      <label htmlFor="sowingDate" className="block text-sm font-medium text-gray-700 mb-1">Sowing Date</label>
                      <input 
                        id="sowingDate"
                        type="date" required value={sowingDate} onChange={e => setSowingDate(e.target.value)}
                        max={new Date().toISOString().split('T')[0]}
                        className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-farm-DEFAULT/20 focus:border-farm-DEFAULT transition-shadow bg-gray-50/50"
                      />
                      <p className="text-xs text-gray-500 mt-2">Required for accurate growth stage context.</p>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}

            {step === 2 && (
              <motion.div key="step2" variants={stepVariants} initial="initial" animate="animate" exit="exit" className="p-8 md:p-12 flex flex-col h-full">
                <div className="text-center mb-8">
                  <div className="w-16 h-16 bg-farm-light text-farm-DEFAULT rounded-2xl flex items-center justify-center mx-auto mb-6">
                    <MapIcon size={32} />
                  </div>
                  <h2 className="text-3xl font-bold tracking-tight text-gray-900 mb-2">Draw your field</h2>
                  <p className="text-gray-500">Define the exact boundary for satellite monitoring.</p>
                </div>
                
                <div className="flex-1 rounded-2xl overflow-hidden border border-gray-200 min-h-[400px]">
                  <SetupMap onBoundaryChange={(b, c) => { setBoundary(b); setCenter(c); }} />
                </div>
              </motion.div>
            )}

            {step === 3 && (
              <motion.div key="step3" variants={stepVariants} initial="initial" animate="animate" exit="exit" className="p-8 md:p-12">
                <div className="max-w-xl mx-auto text-center">
                  <div className="w-20 h-20 bg-farm-DEFAULT text-white rounded-full flex items-center justify-center mx-auto mb-8 shadow-xl shadow-farm-DEFAULT/20">
                    <Sprout size={40} />
                  </div>
                  <h2 className="text-3xl font-bold tracking-tight text-gray-900 mb-2">Ready to create</h2>
                  <p className="text-gray-500 mb-10">We'll generate your Digital Farm Twin based on these details.</p>
                  
                  <div className="bg-gray-50 rounded-2xl p-6 text-left space-y-4 mb-10">
                    <div className="flex justify-between pb-4 border-b border-gray-200">
                      <span className="text-gray-500">Name</span>
                      <span className="font-medium text-gray-900">{name}</span>
                    </div>
                    <div className="flex justify-between pb-4 border-b border-gray-200">
                      <span className="text-gray-500">Crop</span>
                      <span className="font-medium text-gray-900 capitalize">{crop}</span>
                    </div>
                    <div className="flex justify-between pb-4 border-b border-gray-200">
                      <span className="text-gray-500">Sown</span>
                      <span className="font-medium text-gray-900">{sowingDate}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Boundary</span>
                      <span className="font-medium text-farm-DEFAULT flex items-center gap-1"><CheckCircle2 size={16}/> Drawn</span>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Footer Navigation */}
        <div className="mt-8 flex justify-between items-center px-4 max-w-4xl mx-auto w-full">
          {step > 1 ? (
            <button onClick={handleBack} disabled={loading} className="flex items-center gap-2 text-gray-500 hover:text-gray-900 font-medium transition-colors px-4 py-2">
              <ArrowLeft size={20} /> Back
            </button>
          ) : <div />}
          
          {step < 3 ? (
            <button onClick={handleNext} className="bg-gray-900 hover:bg-black text-white px-8 py-3 rounded-xl font-medium transition-colors flex items-center gap-2 shadow-md">
              Continue <ArrowRight size={20} />
            </button>
          ) : (
            <button onClick={handleSubmit} disabled={loading} className="bg-farm-DEFAULT hover:bg-farm-secondary text-white px-8 py-3 rounded-xl font-medium transition-all shadow-lg shadow-farm-DEFAULT/20 flex items-center gap-2 hover:scale-[1.02] active:scale-[0.98] disabled:opacity-70 disabled:scale-100">
              {loading ? <Loader2 className="animate-spin" size={20} /> : <Sprout size={20} />}
              {loading ? 'Creating Farm...' : 'Create Digital Farm Twin'}
            </button>
          )}
        </div>

      </div>
    </div>
  );
}

// Simple fallback icon
function AlertTriangle({ className }: { className?: string }) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z" />
      <path d="M12 9v4" />
      <path d="M12 17h.01" />
    </svg>
  );
}
