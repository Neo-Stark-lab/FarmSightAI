import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '../api/client';
import SetupMap from '../components/Map/SetupMap';
import { Sprout, Loader2 } from 'lucide-react';

export default function FarmSetupPage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [name, setName] = useState('');
  const [crop, setCrop] = useState<'rice' | 'groundnut' | 'maize'>('rice');
  const [sowingDate, setSowingDate] = useState('');
  
  const [boundary, setBoundary] = useState<number[][][] | null>(null);
  const [center, setCenter] = useState<[number, number] | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !boundary || !center || !sowingDate) {
      setError("Please fill out all fields and draw a farm boundary on the map.");
      return;
    }
    
    setLoading(true);
    setError(null);
    try {
      const idempotencyKey = crypto.randomUUID();
      const res = await apiClient.createFarm({
        name,
        crop,
        sowing_date: sowingDate,
        location: { type: 'Point', coordinates: center },
        boundary: { type: 'Polygon', coordinates: boundary },
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone
      }, idempotencyKey);
      
      navigate(`/farms/${res.farm.id}`);
    } catch (err: any) {
      setError(err.message || "Failed to create farm.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto p-6 w-full">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
          <Sprout className="text-farm-DEFAULT" />
          Create Your Farm
        </h1>
        <p className="text-gray-600 mt-2">Define your farm details to start monitoring water-stress zones.</p>
      </div>

      {error && (
        <div className="bg-red-50 border-l-4 border-red-500 p-4 mb-6">
          <p className="text-red-700">{error}</p>
        </div>
      )}

      <form onSubmit={handleSubmit} className="grid md:grid-cols-2 gap-8">
        <div className="space-y-6 bg-white p-6 rounded-xl shadow-sm border border-gray-200">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Farm Name</label>
            <input 
              type="text"
              required
              value={name}
              onChange={e => setName(e.target.value)}
              className="w-full border border-gray-300 rounded-md p-2 focus:ring-farm-DEFAULT focus:border-farm-DEFAULT"
              placeholder="e.g., North Field"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Crop Type</label>
            <select 
              value={crop}
              onChange={e => setCrop(e.target.value as any)}
              className="w-full border border-gray-300 rounded-md p-2 focus:ring-farm-DEFAULT focus:border-farm-DEFAULT"
            >
              <option value="rice">Rice</option>
              <option value="groundnut">Groundnut</option>
              <option value="maize">Maize</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Sowing Date</label>
            <input 
              type="date"
              required
              value={sowingDate}
              onChange={e => setSowingDate(e.target.value)}
              max={new Date().toISOString().split('T')[0]}
              className="w-full border border-gray-300 rounded-md p-2 focus:ring-farm-DEFAULT focus:border-farm-DEFAULT"
            />
            <p className="text-xs text-gray-500 mt-1">Cannot be a future date.</p>
          </div>

          <div className="pt-4">
            <button 
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center bg-farm-DEFAULT hover:bg-farm-dark text-white font-bold py-3 px-4 rounded-md shadow transition-colors disabled:opacity-50"
            >
              {loading ? <Loader2 className="animate-spin mr-2" /> : null}
              {loading ? 'Creating...' : 'Save & Analyze Farm'}
            </button>
          </div>
        </div>

        <div className="flex flex-col">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Draw Farm Boundary
          </label>
          <p className="text-sm text-gray-500 mb-3">
            Use the polygon or rectangle tool to draw your farm's exact boundary.
          </p>
          <SetupMap onBoundaryChange={(b, c) => { setBoundary(b); setCenter(c); }} />
          {!boundary && (
            <p className="text-red-500 text-sm mt-2 font-medium">Boundary required</p>
          )}
        </div>
      </form>
    </div>
  );
}
