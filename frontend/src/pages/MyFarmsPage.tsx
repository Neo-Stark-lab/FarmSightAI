import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Plus, Map as MapIcon, Calendar, ArrowRight, AlertTriangle } from 'lucide-react';
import type { Farm } from '../api/types';
import { demoFarms } from '../utils/demoPersistence';

export default function MyFarmsPage() {
  const [farms, setFarms] = useState<Farm[]>([]);

  useEffect(() => {
    // Load persisted demo farms
    setFarms(demoFarms.getFarms());
  }, []);

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1, transition: { staggerChildren: 0.1 } }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 15 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.6 } }
  };

  return (
    <div className="flex-1 bg-surface py-12 px-6 min-h-[calc(100vh-73px)]">
      <div className="max-w-6xl mx-auto">
        
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between mb-12 gap-6">
          <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.5 }}>
            <h1 className="text-3xl md:text-4xl font-bold tracking-tight text-gray-900 mb-2">My Farms</h1>
            <p className="text-gray-600 text-lg">Your Digital Farm Twins</p>
          </motion.div>
          
          <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.5 }}>
            <Link 
              to="/farms/new" 
              className="bg-farm-DEFAULT hover:bg-farm-dark text-white px-6 py-3 rounded-xl font-medium shadow-lg shadow-farm-DEFAULT/20 flex items-center gap-2 transition-all hover:scale-[1.02] active:scale-[0.98]"
            >
              <Plus size={20} />
              Add Farm
            </Link>
          </motion.div>
        </div>

        {farms.length === 0 ? (
          <motion.div 
            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}
            className="bg-white border border-gray-200 rounded-3xl p-12 text-center max-w-2xl mx-auto shadow-sm"
          >
            <div className="w-20 h-20 bg-farm-light rounded-full flex items-center justify-center mx-auto mb-6 text-farm-DEFAULT">
              <MapIcon size={32} />
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-3">No farms yet</h2>
            <p className="text-gray-600 mb-8 max-w-md mx-auto">
              Create your first Digital Farm Twin to start monitoring vegetation health, water stress, and weather data.
            </p>
            <Link 
              to="/farms/new" 
              className="bg-gray-900 hover:bg-black text-white px-8 py-3 rounded-xl font-medium transition-colors inline-flex items-center gap-2"
            >
              Add your first farm
            </Link>
          </motion.div>
        ) : (
          <motion.div 
            variants={containerVariants}
            initial="hidden"
            animate="visible"
            className="grid md:grid-cols-2 lg:grid-cols-3 gap-6"
          >
            {farms.map(farm => {
              const area = 'N/A'; // Calculated from backend
              
              // We just show a dummy status for demo list
              const hasAnalysis = false;
              const isFailed = false;
              const isStale = false;

              return (
                <motion.div 
                  key={farm.id}
                  variants={itemVariants}
                  className="bg-white border border-gray-200 rounded-3xl p-6 hover:shadow-xl hover:shadow-gray-200/50 hover:border-gray-300 transition-all duration-300 group flex flex-col h-full"
                >
                  <div className="flex justify-between items-start mb-6">
                    <div>
                      <h3 className="text-xl font-bold text-gray-900 mb-1">{farm.name}</h3>
                      <p className="text-gray-500 text-sm flex items-center gap-1.5 capitalize">
                        <MapIcon size={14} /> {area} &middot; {farm.crop}
                      </p>
                    </div>
                    {/* Tiny Map Preview Placeholder */}
                    <div className="w-12 h-12 bg-gray-100 rounded-xl flex items-center justify-center text-gray-400">
                      <MapIcon size={20} />
                    </div>
                  </div>

                  <div className="space-y-4 mb-8 flex-grow">
                    {hasAnalysis ? (
                      <div className={`p-4 rounded-xl flex items-start gap-3 ${isFailed ? 'bg-red-50 text-red-900' : isStale ? 'bg-amber-50 text-amber-900' : 'bg-farm-light text-farm-dark'}`}>
                        {isFailed ? <AlertTriangle size={18} className="mt-0.5 shrink-0" /> : <ActivityIcon className="mt-0.5 shrink-0" size={18} />}
                        <div>
                          <p className="text-sm font-semibold">{isFailed ? 'Analysis Failed' : isStale ? 'Partial Analysis' : 'Analysis Complete'}</p>
                        </div>
                      </div>
                    ) : (
                      <div className="p-4 rounded-xl bg-gray-50 text-gray-600 flex items-start gap-3">
                        <Calendar size={18} className="mt-0.5 shrink-0 text-gray-400" />
                        <div>
                          <p className="text-sm font-medium">No analysis yet</p>
                          <p className="text-xs mt-0.5 text-gray-500">Run an analysis to get insights</p>
                        </div>
                      </div>
                    )}
                  </div>

                  <Link 
                    to={`/farms/${farm.id}`} 
                    className="mt-auto w-full py-3 px-4 bg-gray-50 hover:bg-farm-DEFAULT hover:text-white text-gray-700 font-medium rounded-xl transition-colors flex items-center justify-between group-hover:bg-farm-DEFAULT group-hover:text-white"
                  >
                    Open Farm <ArrowRight size={18} className="transition-transform group-hover:translate-x-1" />
                  </Link>
                </motion.div>
              );
            })}
          </motion.div>
        )}
      </div>
    </div>
  );
}

// Simple icon for activity
function ActivityIcon({ className, size }: { className?: string, size?: number }) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width={size || 24} height={size || 24} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
    </svg>
  );
}
