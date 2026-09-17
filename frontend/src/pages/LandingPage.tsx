import { Link } from 'react-router-dom';
import { Sprout, Map, Activity, ShieldCheck } from 'lucide-react';

export default function LandingPage() {
  return (
    <div className="flex-grow flex flex-col items-center justify-center p-6 bg-gradient-to-b from-farm-light to-white">
      <div className="max-w-3xl text-center space-y-8">
        <Sprout size={80} className="mx-auto text-farm-dark" />
        
        <h1 className="text-5xl font-extrabold text-gray-900 tracking-tight">
          FarmSight AI
        </h1>
        
        <p className="text-2xl text-farm-dark font-medium">
          "See the problem. Understand why. Know what to do."
        </p>
        
        <p className="text-lg text-gray-600 max-w-2xl mx-auto">
          Create a Digital Farm Twin to monitor your crops. We combine satellite imagery, weather data, and agricultural rules to provide zone-level water-stress intelligence and explainable recommendations designed specifically for small and marginal farmers.
        </p>

        <div className="grid md:grid-cols-3 gap-6 pt-8 pb-12">
          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex flex-col items-center text-center">
            <div className="bg-blue-50 p-3 rounded-full mb-4">
              <Map className="text-blue-600" size={32} />
            </div>
            <h3 className="font-semibold text-lg mb-2">Digital Farm Twin</h3>
            <p className="text-gray-500 text-sm">Visualize your farm zones and boundaries on an interactive map.</p>
          </div>
          
          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex flex-col items-center text-center">
            <div className="bg-orange-50 p-3 rounded-full mb-4">
              <Activity className="text-orange-600" size={32} />
            </div>
            <h3 className="font-semibold text-lg mb-2">Water-Stress Intelligence</h3>
            <p className="text-gray-500 text-sm">Pinpoint exactly which zones need attention right now.</p>
          </div>
          
          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex flex-col items-center text-center">
            <div className="bg-green-50 p-3 rounded-full mb-4">
              <ShieldCheck className="text-green-600" size={32} />
            </div>
            <h3 className="font-semibold text-lg mb-2">Explainable Recommendations</h3>
            <p className="text-gray-500 text-sm">Understand exactly why an action is recommended with clear evidence.</p>
          </div>
        </div>

        <Link 
          to="/setup" 
          className="inline-block bg-farm-DEFAULT hover:bg-farm-dark text-white font-bold py-4 px-10 rounded-full text-xl shadow-lg transition-transform hover:scale-105"
        >
          Create Your Farm
        </Link>
      </div>
    </div>
  );
}
